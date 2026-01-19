#!/usr/bin/env python3
"""CLI script for exporting YOLOv8 card detector to ONNX format.

This script exports a trained YOLOv8 model to ONNX format for mobile
deployment. Supports various optimization options including quantization.

Usage:
    # Export with default settings
    uv run python scripts/export_to_onnx.py \\
        --weights runs/detect/card_detector/train/weights/best.pt

    # Export with INT8 quantization for mobile
    uv run python scripts/export_to_onnx.py \\
        --weights runs/detect/card_detector/train/weights/best.pt \\
        --int8 \\
        --output models/card_detector_int8.onnx

    # Export with FP16 for GPU inference
    uv run python scripts/export_to_onnx.py \\
        --weights runs/detect/card_detector/train/weights/best.pt \\
        --half \\
        --output models/card_detector_fp16.onnx

    # Export with custom image size
    uv run python scripts/export_to_onnx.py \\
        --weights runs/detect/card_detector/train/weights/best.pt \\
        --imgsz 416 \\
        --output models/card_detector_416.onnx

Requirements:
    Install recognition extras: uv sync --extra recognition
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the script.

    Args:
        verbose: If True, use DEBUG level; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def export_to_onnx(
    weights_path: Path,
    output_path: Path | None = None,
    image_size: int = 640,
    opset: int = 17,
    simplify: bool = True,
    dynamic: bool = True,
    half: bool = False,
    int8: bool = False,
    batch_size: int = 1,
    nms: bool = False,
    device: str = "",
) -> Path:
    """Export YOLOv8 model to ONNX format.

    Args:
        weights_path: Path to trained weights (.pt file).
        output_path: Path for exported ONNX model. Auto-generated if None.
        image_size: Export image size.
        opset: ONNX opset version.
        simplify: Simplify ONNX graph.
        dynamic: Enable dynamic input shapes.
        half: Export as FP16.
        int8: Export as INT8 (quantized).
        batch_size: Export batch size.
        nms: Include NMS in exported model.
        device: Device for export.

    Returns:
        Path to exported ONNX model.

    Raises:
        ImportError: If ultralytics is not installed.
        FileNotFoundError: If weights don't exist.
    """
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise ImportError(
            "ultralytics is required for export. "
            "Install with: uv sync --extra recognition"
        ) from e

    logger = logging.getLogger(__name__)

    # Validate weights
    if not weights_path.exists():
        raise FileNotFoundError(f"Weights not found: {weights_path}")

    # Load model
    logger.info(f"Loading model from {weights_path}")
    model = YOLO(str(weights_path))

    # Determine output path
    if output_path is None:
        suffix = ""
        if int8:
            suffix = "_int8"
        elif half:
            suffix = "_fp16"
        output_path = weights_path.parent / f"best{suffix}.onnx"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Log export configuration
    logger.info("=" * 60)
    logger.info("EXPORT CONFIGURATION")
    logger.info("=" * 60)
    logger.info(f"Input weights: {weights_path}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Image size: {image_size}")
    logger.info(f"ONNX opset: {opset}")
    logger.info(f"Simplify: {simplify}")
    logger.info(f"Dynamic shapes: {dynamic}")
    logger.info(f"FP16 (half): {half}")
    logger.info(f"INT8 quantization: {int8}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Include NMS: {nms}")
    logger.info("=" * 60)

    # Export model
    logger.info("Exporting model to ONNX...")
    export_path = model.export(
        format="onnx",
        imgsz=image_size,
        opset=opset,
        simplify=simplify,
        dynamic=dynamic,
        half=half,
        int8=int8,
        batch=batch_size,
        nms=nms,
        device=device or None,
    )

    # Move to target path if different
    export_path = Path(export_path)
    if export_path != output_path:
        import shutil

        shutil.move(str(export_path), str(output_path))

    logger.info(f"Export complete: {output_path}")

    # Get model size
    model_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Model size: {model_size_mb:.2f} MB")

    # Save class names for inference
    class_names_path = output_path.with_suffix(".json")
    class_names = list(model.names.values())
    with open(class_names_path, "w") as f:
        json.dump({"names": class_names, "nc": len(class_names)}, f, indent=2)
    logger.info(f"Class names saved: {class_names_path}")

    return output_path


def validate_onnx(
    onnx_path: Path,
    test_image_size: int = 640,
) -> bool:
    """Validate exported ONNX model.

    Args:
        onnx_path: Path to ONNX model.
        test_image_size: Image size for test inference.

    Returns:
        True if validation passed.
    """
    logger = logging.getLogger(__name__)

    try:
        import numpy as np
        import onnx
        import onnxruntime as ort
    except ImportError as e:
        logger.warning(f"Skipping ONNX validation: {e}")
        return True

    logger.info("Validating ONNX model...")

    # Check ONNX model
    try:
        model = onnx.load(str(onnx_path))
        onnx.checker.check_model(model)
        logger.info("ONNX model structure: OK")
    except Exception as e:
        logger.error(f"ONNX validation failed: {e}")
        return False

    # Test inference
    try:
        session = ort.InferenceSession(str(onnx_path))

        # Get input info
        input_info = session.get_inputs()[0]
        input_name = input_info.name
        input_shape = input_info.shape

        # Create test input
        batch_size = input_shape[0] if isinstance(input_shape[0], int) else 1
        channels = input_shape[1] if isinstance(input_shape[1], int) else 3
        height = input_shape[2] if isinstance(input_shape[2], int) else test_image_size
        width = input_shape[3] if isinstance(input_shape[3], int) else test_image_size

        test_input = np.random.rand(batch_size, channels, height, width).astype(
            np.float32
        )

        # Run inference
        import time

        start = time.perf_counter()
        outputs = session.run(None, {input_name: test_input})
        inference_time = (time.perf_counter() - start) * 1000

        logger.info(f"Test inference: OK ({inference_time:.2f} ms)")
        logger.info(f"Output shape: {outputs[0].shape}")

    except Exception as e:
        logger.error(f"Inference test failed: {e}")
        return False

    logger.info("ONNX validation: PASSED")
    return True


def benchmark_onnx(
    onnx_path: Path,
    image_size: int = 640,
    num_iterations: int = 100,
    warmup: int = 10,
) -> dict:
    """Benchmark ONNX model inference performance.

    Args:
        onnx_path: Path to ONNX model.
        image_size: Image size for benchmark.
        num_iterations: Number of iterations.
        warmup: Warmup iterations.

    Returns:
        Dictionary with benchmark results.
    """
    logger = logging.getLogger(__name__)

    try:
        import numpy as np
        import onnxruntime as ort
    except ImportError as e:
        logger.warning(f"Skipping benchmark: {e}")
        return {}

    logger.info(f"Benchmarking ONNX model ({num_iterations} iterations)...")

    # Create session
    session = ort.InferenceSession(str(onnx_path))

    # Get input info
    input_info = session.get_inputs()[0]
    input_name = input_info.name
    input_shape = input_info.shape

    # Create test input
    batch_size = input_shape[0] if isinstance(input_shape[0], int) else 1
    channels = input_shape[1] if isinstance(input_shape[1], int) else 3
    height = input_shape[2] if isinstance(input_shape[2], int) else image_size
    width = input_shape[3] if isinstance(input_shape[3], int) else image_size

    test_input = np.random.rand(batch_size, channels, height, width).astype(np.float32)

    # Warmup
    for _ in range(warmup):
        session.run(None, {input_name: test_input})

    # Benchmark
    import time

    times = []
    for _ in range(num_iterations):
        start = time.perf_counter()
        session.run(None, {input_name: test_input})
        times.append((time.perf_counter() - start) * 1000)

    # Calculate statistics
    times_array = np.array(times)
    results = {
        "mean_ms": float(np.mean(times_array)),
        "std_ms": float(np.std(times_array)),
        "min_ms": float(np.min(times_array)),
        "max_ms": float(np.max(times_array)),
        "p50_ms": float(np.percentile(times_array, 50)),
        "p95_ms": float(np.percentile(times_array, 95)),
        "p99_ms": float(np.percentile(times_array, 99)),
        "fps": float(1000 / np.mean(times_array)),
    }

    logger.info("=" * 60)
    logger.info("BENCHMARK RESULTS")
    logger.info("=" * 60)
    logger.info(f"Mean: {results['mean_ms']:.2f} ms")
    logger.info(f"Std: {results['std_ms']:.2f} ms")
    logger.info(f"Min: {results['min_ms']:.2f} ms")
    logger.info(f"Max: {results['max_ms']:.2f} ms")
    logger.info(f"P50: {results['p50_ms']:.2f} ms")
    logger.info(f"P95: {results['p95_ms']:.2f} ms")
    logger.info(f"P99: {results['p99_ms']:.2f} ms")
    logger.info(f"FPS: {results['fps']:.2f}")
    logger.info("=" * 60)

    return results


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Export YOLOv8 card detector to ONNX format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input/output arguments
    parser.add_argument(
        "--weights",
        type=Path,
        required=True,
        help="Path to trained weights (.pt file)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Path for exported ONNX model (default: auto)",
    )

    # Export settings
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Export image size (default: 640)",
    )

    parser.add_argument(
        "--opset",
        type=int,
        default=17,
        help="ONNX opset version (default: 17)",
    )

    parser.add_argument(
        "--no-simplify",
        action="store_true",
        help="Disable ONNX graph simplification",
    )

    parser.add_argument(
        "--no-dynamic",
        action="store_true",
        help="Disable dynamic input shapes",
    )

    parser.add_argument(
        "--half",
        action="store_true",
        help="Export as FP16",
    )

    parser.add_argument(
        "--int8",
        action="store_true",
        help="Export as INT8 (quantized)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Export batch size (default: 1)",
    )

    parser.add_argument(
        "--nms",
        action="store_true",
        help="Include NMS in exported model",
    )

    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Device for export (default: auto)",
    )

    # Validation and benchmark
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate exported model",
    )

    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Benchmark exported model",
    )

    parser.add_argument(
        "--benchmark-iterations",
        type=int,
        default=100,
        help="Benchmark iterations (default: 100)",
    )

    # Logging
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Run export
    try:
        onnx_path = export_to_onnx(
            weights_path=args.weights,
            output_path=args.output,
            image_size=args.imgsz,
            opset=args.opset,
            simplify=not args.no_simplify,
            dynamic=not args.no_dynamic,
            half=args.half,
            int8=args.int8,
            batch_size=args.batch_size,
            nms=args.nms,
            device=args.device,
        )

        # Validate if requested
        if args.validate:
            if not validate_onnx(onnx_path, args.imgsz):
                logger.error("Validation failed")
                return 1

        # Benchmark if requested
        if args.benchmark:
            benchmark_onnx(
                onnx_path,
                args.imgsz,
                args.benchmark_iterations,
            )

        logger.info(f"Export successful: {onnx_path}")
        return 0

    except ImportError as e:
        logger.error(str(e))
        return 1
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception(f"Export failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
