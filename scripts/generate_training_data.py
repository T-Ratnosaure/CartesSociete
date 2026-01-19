#!/usr/bin/env python3
"""CLI script for generating card recognition training data.

This script generates YOLO-format training data by applying augmentations
to card images. The output can be used directly with YOLOv5/v8 training.

Usage:
    uv run python scripts/generate_training_data.py \\
        --images-dir ./assets/images \\
        --output-dir ./data/training \\
        --augmentations-per-card 100

    # Generate samples for a single card
    uv run python scripts/generate_training_data.py \\
        --images-dir ./assets/images \\
        --output-dir ./data/training \\
        --sample-card lapin_gardien_des_carottes_1 \\
        --sample-count 10
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.recognition.augmentation import (  # noqa: E402
    CardAugmentationPipeline,
    create_aggressive_pipeline,
    create_conservative_pipeline,
)
from src.recognition.dataset_generator import SyntheticDatasetGenerator  # noqa: E402


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


def create_pipeline_from_preset(
    preset: str,
    output_size: tuple[int, int],
) -> CardAugmentationPipeline:
    """Create augmentation pipeline from preset name.

    Args:
        preset: One of "default", "conservative", "aggressive".
        output_size: Target output image size.

    Returns:
        Configured augmentation pipeline.
    """
    if preset == "conservative":
        pipeline = create_conservative_pipeline()
    elif preset == "aggressive":
        pipeline = create_aggressive_pipeline()
    else:
        pipeline = CardAugmentationPipeline()

    # Update output size
    pipeline.config.output_size = output_size
    return pipeline


def run_full_generation(
    images_dir: Path,
    output_dir: Path,
    augmentations_per_card: int,
    val_split: float,
    seed: int,
    preset: str,
    output_size: tuple[int, int],
) -> int:
    """Run full dataset generation.

    Args:
        images_dir: Directory containing card images.
        output_dir: Directory for output dataset.
        augmentations_per_card: Number of augmentations per card.
        val_split: Fraction for validation set.
        seed: Random seed.
        preset: Augmentation preset name.
        output_size: Target image size.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger = logging.getLogger(__name__)

    # Validate inputs
    if not images_dir.exists():
        logger.error(f"Images directory does not exist: {images_dir}")
        return 1

    # Create pipeline
    pipeline = create_pipeline_from_preset(preset, output_size)

    # Create generator
    generator = SyntheticDatasetGenerator(
        images_dir=images_dir,
        output_dir=output_dir,
        augmentation_pipeline=pipeline,
    )

    # Run generation
    logger.info("Starting dataset generation...")
    logger.info(f"  Images directory: {images_dir}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info(f"  Augmentations per card: {augmentations_per_card}")
    logger.info(f"  Validation split: {val_split}")
    logger.info(f"  Preset: {preset}")
    logger.info(f"  Output size: {output_size}")

    try:
        stats = generator.generate(
            augmentations_per_card=augmentations_per_card,
            val_split=val_split,
            seed=seed,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return 1

    # Report results
    logger.info("")
    logger.info("=" * 50)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Total cards in repository: {stats.total_cards}")
    logger.info(f"Cards processed: {stats.cards_processed}")
    logger.info(f"Cards skipped: {stats.cards_skipped}")
    logger.info(f"Total images generated: {stats.images_generated}")
    logger.info(f"Training images: {stats.train_images}")
    logger.info(f"Validation images: {stats.val_images}")

    if stats.skipped_cards:
        logger.warning("")
        logger.warning("Skipped cards (missing images):")
        for card_id in stats.skipped_cards[:10]:
            logger.warning(f"  - {card_id}")
        if len(stats.skipped_cards) > 10:
            logger.warning(f"  ... and {len(stats.skipped_cards) - 10} more")

    logger.info("")
    logger.info(f"Dataset saved to: {output_dir}")
    logger.info(f"Use data.yaml for YOLO training: {output_dir / 'data.yaml'}")

    return 0


def run_sample_generation(
    images_dir: Path,
    output_dir: Path,
    card_id: str,
    sample_count: int,
    seed: int,
    preset: str,
    output_size: tuple[int, int],
) -> int:
    """Generate samples for a single card.

    Args:
        images_dir: Directory containing card images.
        output_dir: Directory for output.
        card_id: Card ID to generate samples for.
        sample_count: Number of samples to generate.
        seed: Random seed.
        preset: Augmentation preset name.
        output_size: Target image size.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger = logging.getLogger(__name__)

    # Create pipeline
    pipeline = create_pipeline_from_preset(preset, output_size)

    # Create generator
    generator = SyntheticDatasetGenerator(
        images_dir=images_dir,
        output_dir=output_dir,
        augmentation_pipeline=pipeline,
    )

    # Run sample generation
    logger.info(f"Generating {sample_count} samples for card: {card_id}")

    try:
        paths = generator.generate_sample(
            card_id=card_id,
            count=sample_count,
            seed=seed,
        )
    except ValueError as e:
        logger.error(f"Sample generation failed: {e}")
        return 1

    logger.info(f"Generated {len(paths)} samples")
    for path in paths[:5]:
        logger.info(f"  - {path}")
    if len(paths) > 5:
        logger.info(f"  ... and {len(paths) - 5} more")

    return 0


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Generate YOLO training data for card recognition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--images-dir",
        type=Path,
        required=True,
        help="Directory containing original card images",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for output dataset",
    )

    parser.add_argument(
        "--augmentations-per-card",
        type=int,
        default=100,
        help="Number of augmented images per card (default: 100)",
    )

    parser.add_argument(
        "--val-split",
        type=float,
        default=0.2,
        help="Fraction of images for validation (default: 0.2)",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    parser.add_argument(
        "--preset",
        choices=["default", "conservative", "aggressive"],
        default="default",
        help="Augmentation preset (default: default)",
    )

    parser.add_argument(
        "--output-size",
        type=int,
        nargs=2,
        default=[640, 640],
        metavar=("WIDTH", "HEIGHT"),
        help="Output image size (default: 640 640)",
    )

    parser.add_argument(
        "--sample-card",
        type=str,
        help="Generate samples for a single card instead of full dataset",
    )

    parser.add_argument(
        "--sample-count",
        type=int,
        default=10,
        help="Number of samples to generate (with --sample-card, default: 10)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Convert output size to tuple
    output_size = tuple(args.output_size)

    # Run appropriate mode
    if args.sample_card:
        return run_sample_generation(
            images_dir=args.images_dir,
            output_dir=args.output_dir,
            card_id=args.sample_card,
            sample_count=args.sample_count,
            seed=args.seed,
            preset=args.preset,
            output_size=output_size,
        )
    else:
        return run_full_generation(
            images_dir=args.images_dir,
            output_dir=args.output_dir,
            augmentations_per_card=args.augmentations_per_card,
            val_split=args.val_split,
            seed=args.seed,
            preset=args.preset,
            output_size=output_size,
        )


if __name__ == "__main__":
    sys.exit(main())
