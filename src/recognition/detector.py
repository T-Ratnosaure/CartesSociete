"""YOLOv8 card detector wrapper for inference.

This module provides a clean interface for card detection using YOLOv8
or ONNX models. It supports both training-time inference and production
deployment with ONNX Runtime.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from .config import InferenceConfig

if TYPE_CHECKING:
    from ultralytics import YOLO

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single card detection result.

    Attributes:
        card_id: Detected card class name/ID.
        class_index: Detected card class index.
        confidence: Detection confidence score (0-1).
        bbox: Bounding box as (x1, y1, x2, y2) in pixels.
        bbox_normalized: Bounding box as (x_center, y_center, w, h) normalized.
    """

    card_id: str
    class_index: int
    confidence: float
    bbox: tuple[int, int, int, int]
    bbox_normalized: tuple[float, float, float, float]


@dataclass
class DetectionResult:
    """Detection results for a single image.

    Attributes:
        detections: List of card detections.
        image_shape: Original image shape (height, width, channels).
        inference_time_ms: Inference time in milliseconds.
    """

    detections: list[Detection]
    image_shape: tuple[int, int, int]
    inference_time_ms: float


class CardDetector:
    """YOLOv8-based card detector.

    Provides card detection using either a PyTorch YOLOv8 model or
    an ONNX model for optimized inference.

    Example:
        >>> detector = CardDetector.from_checkpoint("runs/detect/train/weights/best.pt")
        >>> result = detector.detect(image)
        >>> for detection in result.detections:
        ...     print(f"{detection.card_id}: {detection.confidence:.2f}")
    """

    def __init__(
        self,
        model: "YOLO",
        class_names: list[str],
        config: InferenceConfig | None = None,
    ) -> None:
        """Initialize the detector.

        Args:
            model: Loaded YOLO model.
            class_names: List of class names indexed by class ID.
            config: Inference configuration.
        """
        self._model = model
        self._class_names = class_names
        self._config = config or InferenceConfig()

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: Path | str,
        config: InferenceConfig | None = None,
    ) -> "CardDetector":
        """Load detector from a training checkpoint.

        Args:
            checkpoint_path: Path to .pt weights file.
            config: Inference configuration.

        Returns:
            Initialized CardDetector.

        Raises:
            ImportError: If ultralytics is not installed.
            FileNotFoundError: If checkpoint doesn't exist.
        """
        try:
            from ultralytics import YOLO
        except ImportError as e:
            raise ImportError(
                "ultralytics is required for CardDetector. "
                "Install with: pip install ultralytics"
            ) from e

        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        logger.info(f"Loading model from {checkpoint_path}")
        model = YOLO(str(checkpoint_path))

        # Extract class names from model
        class_names = list(model.names.values())

        return cls(model, class_names, config)

    @classmethod
    def from_onnx(
        cls,
        onnx_path: Path | str,
        class_names: list[str],
        config: InferenceConfig | None = None,
    ) -> "ONNXCardDetector":
        """Load detector from an ONNX model.

        Args:
            onnx_path: Path to ONNX model file.
            class_names: List of class names indexed by class ID.
            config: Inference configuration.

        Returns:
            Initialized ONNXCardDetector.
        """
        return ONNXCardDetector(onnx_path, class_names, config)

    def detect(
        self,
        image: np.ndarray,
        confidence_threshold: float | None = None,
        iou_threshold: float | None = None,
    ) -> DetectionResult:
        """Detect cards in an image.

        Args:
            image: Input image as numpy array (BGR or RGB).
            confidence_threshold: Override default confidence threshold.
            iou_threshold: Override default IoU threshold.

        Returns:
            DetectionResult containing all detected cards.
        """
        conf = confidence_threshold or self._config.confidence_threshold
        iou = iou_threshold or self._config.iou_threshold

        # Run inference
        results = self._model.predict(
            image,
            conf=conf,
            iou=iou,
            max_det=self._config.max_detections,
            device=self._config.device or None,
            half=self._config.half,
            verbose=self._config.verbose,
        )

        # Parse results
        result = results[0]
        detections = self._parse_results(result, image.shape)

        return DetectionResult(
            detections=detections,
            image_shape=image.shape,
            inference_time_ms=result.speed.get("inference", 0.0),
        )

    def detect_batch(
        self,
        images: list[np.ndarray],
        confidence_threshold: float | None = None,
        iou_threshold: float | None = None,
    ) -> list[DetectionResult]:
        """Detect cards in multiple images.

        Args:
            images: List of input images.
            confidence_threshold: Override default confidence threshold.
            iou_threshold: Override default IoU threshold.

        Returns:
            List of DetectionResult, one per image.
        """
        conf = confidence_threshold or self._config.confidence_threshold
        iou = iou_threshold or self._config.iou_threshold

        # Run batch inference
        results = self._model.predict(
            images,
            conf=conf,
            iou=iou,
            max_det=self._config.max_detections,
            device=self._config.device or None,
            half=self._config.half,
            verbose=self._config.verbose,
        )

        # Parse results for each image
        detection_results = []
        for result, image in zip(results, images, strict=True):
            detections = self._parse_results(result, image.shape)
            detection_results.append(
                DetectionResult(
                    detections=detections,
                    image_shape=image.shape,
                    inference_time_ms=result.speed.get("inference", 0.0),
                )
            )

        return detection_results

    def _parse_results(
        self,
        result: "YOLO",
        image_shape: tuple[int, ...],
    ) -> list[Detection]:
        """Parse YOLO results into Detection objects.

        Args:
            result: YOLO result object.
            image_shape: Original image shape for normalization.

        Returns:
            List of Detection objects.
        """
        detections = []
        height, width = image_shape[:2]

        if result.boxes is None:
            return detections

        for box in result.boxes:
            # Get box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

            # Get class and confidence
            class_idx = int(box.cls[0].cpu().numpy())
            confidence = float(box.conf[0].cpu().numpy())

            # Calculate normalized bbox
            x_center = ((x1 + x2) / 2) / width
            y_center = ((y1 + y2) / 2) / height
            w = (x2 - x1) / width
            h = (y2 - y1) / height

            # Get class name
            card_id = (
                self._class_names[class_idx]
                if class_idx < len(self._class_names)
                else f"class_{class_idx}"
            )

            detections.append(
                Detection(
                    card_id=card_id,
                    class_index=class_idx,
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                    bbox_normalized=(x_center, y_center, w, h),
                )
            )

        return detections

    def visualize(
        self,
        image: np.ndarray,
        result: DetectionResult,
        font_scale: float = 0.5,
        thickness: int = 2,
    ) -> np.ndarray:
        """Draw detection results on an image.

        Args:
            image: Input image (will not be modified).
            result: Detection results to visualize.
            font_scale: Font scale for labels.
            thickness: Line thickness for bboxes.

        Returns:
            Image with detection visualizations drawn.
        """
        output = image.copy()

        for detection in result.detections:
            x1, y1, x2, y2 = detection.bbox

            # Draw bbox
            color = (0, 255, 0)  # Green
            cv2.rectangle(output, (x1, y1), (x2, y2), color, thickness)

            # Draw label
            label = f"{detection.card_id}: {detection.confidence:.2f}"
            label_size, _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
            )
            y_label = max(y1 - 10, label_size[1] + 10)

            cv2.rectangle(
                output,
                (x1, y_label - label_size[1] - 5),
                (x1 + label_size[0], y_label + 5),
                color,
                -1,
            )
            cv2.putText(
                output,
                label,
                (x1, y_label),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (0, 0, 0),
                thickness,
            )

        return output


class ONNXCardDetector:
    """ONNX-based card detector for optimized inference.

    Uses ONNX Runtime for inference, suitable for production deployment
    on mobile and edge devices.

    Example:
        >>> detector = ONNXCardDetector("model.onnx", class_names)
        >>> result = detector.detect(image)
    """

    def __init__(
        self,
        onnx_path: Path | str,
        class_names: list[str],
        config: InferenceConfig | None = None,
    ) -> None:
        """Initialize ONNX detector.

        Args:
            onnx_path: Path to ONNX model file.
            class_names: List of class names indexed by class ID.
            config: Inference configuration.

        Raises:
            ImportError: If onnxruntime is not installed.
            FileNotFoundError: If ONNX file doesn't exist.
        """
        try:
            import onnxruntime as ort
        except ImportError as e:
            raise ImportError(
                "onnxruntime is required for ONNXCardDetector. "
                "Install with: pip install onnxruntime"
            ) from e

        onnx_path = Path(onnx_path)
        if not onnx_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {onnx_path}")

        self._class_names = class_names
        self._config = config or InferenceConfig()
        self._onnx_path = onnx_path

        # Create session options
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        )

        # Select providers based on config
        providers = ["CPUExecutionProvider"]
        if self._config.device and "cuda" in self._config.device.lower():
            providers.insert(0, "CUDAExecutionProvider")

        logger.info(f"Loading ONNX model from {onnx_path}")
        self._session = ort.InferenceSession(
            str(onnx_path),
            sess_options,
            providers=providers,
        )

        # Get input/output info
        self._input_name = self._session.get_inputs()[0].name
        self._input_shape = self._session.get_inputs()[0].shape
        self._output_names = [o.name for o in self._session.get_outputs()]

        logger.info(f"ONNX model loaded. Input shape: {self._input_shape}")

    def detect(
        self,
        image: np.ndarray,
        confidence_threshold: float | None = None,
        iou_threshold: float | None = None,
    ) -> DetectionResult:
        """Detect cards in an image.

        Args:
            image: Input image as numpy array (BGR or RGB).
            confidence_threshold: Override default confidence threshold.
            iou_threshold: Override default IoU threshold.

        Returns:
            DetectionResult containing all detected cards.
        """
        import time

        conf = confidence_threshold or self._config.confidence_threshold
        iou = iou_threshold or self._config.iou_threshold

        # Preprocess image
        input_tensor, scale, pad = self._preprocess(image)

        # Run inference
        start_time = time.perf_counter()
        outputs = self._session.run(
            self._output_names, {self._input_name: input_tensor}
        )
        inference_time = (time.perf_counter() - start_time) * 1000

        # Postprocess results
        detections = self._postprocess(outputs[0], image.shape, scale, pad, conf, iou)

        return DetectionResult(
            detections=detections,
            image_shape=image.shape,
            inference_time_ms=inference_time,
        )

    def _preprocess(
        self,
        image: np.ndarray,
    ) -> tuple[np.ndarray, float, tuple[int, int]]:
        """Preprocess image for ONNX inference.

        Args:
            image: Input image.

        Returns:
            Tuple of (input_tensor, scale, padding).
        """
        # Get target size from model input shape
        if self._input_shape[2] is not None:
            target_size = self._input_shape[2]
        else:
            target_size = 640

        # Calculate scale and padding for letterbox
        height, width = image.shape[:2]
        scale = min(target_size / height, target_size / width)
        new_height = int(height * scale)
        new_width = int(width * scale)

        # Resize
        resized = cv2.resize(image, (new_width, new_height))

        # Pad to target size
        pad_h = (target_size - new_height) // 2
        pad_w = (target_size - new_width) // 2

        padded = np.full((target_size, target_size, 3), 114, dtype=np.uint8)
        padded[pad_h : pad_h + new_height, pad_w : pad_w + new_width] = resized

        # Convert to tensor format (NCHW)
        tensor = padded.astype(np.float32) / 255.0
        tensor = tensor.transpose(2, 0, 1)
        tensor = np.expand_dims(tensor, axis=0)

        return tensor, scale, (pad_w, pad_h)

    def _postprocess(
        self,
        output: np.ndarray,
        original_shape: tuple[int, ...],
        scale: float,
        padding: tuple[int, int],
        conf_threshold: float,
        iou_threshold: float,
    ) -> list[Detection]:
        """Postprocess ONNX output to detections.

        Args:
            output: Raw ONNX output.
            original_shape: Original image shape.
            scale: Preprocessing scale factor.
            padding: Preprocessing padding (pad_w, pad_h).
            conf_threshold: Confidence threshold.
            iou_threshold: IoU threshold for NMS.

        Returns:
            List of Detection objects.
        """
        # Output shape: (batch, 4 + num_classes, num_predictions)
        # Transpose to (batch, num_predictions, 4 + num_classes)
        predictions = output[0].transpose()

        # Extract boxes and scores
        boxes = predictions[:, :4]  # x_center, y_center, w, h
        scores = predictions[:, 4:]

        # Get best class and confidence for each prediction
        class_ids = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)

        # Filter by confidence
        mask = confidences > conf_threshold
        boxes = boxes[mask]
        class_ids = class_ids[mask]
        confidences = confidences[mask]

        if len(boxes) == 0:
            return []

        # Convert to xyxy format
        x_centers = boxes[:, 0]
        y_centers = boxes[:, 1]
        widths = boxes[:, 2]
        heights = boxes[:, 3]

        x1 = x_centers - widths / 2
        y1 = y_centers - heights / 2
        x2 = x_centers + widths / 2
        y2 = y_centers + heights / 2

        # Apply NMS
        boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1)
        indices = self._nms(boxes_xyxy, confidences, iou_threshold)

        # Build detections
        detections = []
        pad_w, pad_h = padding
        height, width = original_shape[:2]

        for idx in indices:
            # Remove padding and scale
            bx1 = (x1[idx] - pad_w) / scale
            by1 = (y1[idx] - pad_h) / scale
            bx2 = (x2[idx] - pad_w) / scale
            by2 = (y2[idx] - pad_h) / scale

            # Clip to image bounds
            bx1 = max(0, min(width, bx1))
            by1 = max(0, min(height, by1))
            bx2 = max(0, min(width, bx2))
            by2 = max(0, min(height, by2))

            # Calculate normalized bbox
            x_center = ((bx1 + bx2) / 2) / width
            y_center = ((by1 + by2) / 2) / height
            w = (bx2 - bx1) / width
            h = (by2 - by1) / height

            # Get class name
            class_idx = int(class_ids[idx])
            card_id = (
                self._class_names[class_idx]
                if class_idx < len(self._class_names)
                else f"class_{class_idx}"
            )

            detections.append(
                Detection(
                    card_id=card_id,
                    class_index=class_idx,
                    confidence=float(confidences[idx]),
                    bbox=(int(bx1), int(by1), int(bx2), int(by2)),
                    bbox_normalized=(x_center, y_center, w, h),
                )
            )

        return detections

    def _nms(
        self,
        boxes: np.ndarray,
        scores: np.ndarray,
        iou_threshold: float,
    ) -> list[int]:
        """Apply Non-Maximum Suppression.

        Args:
            boxes: Boxes in xyxy format, shape (N, 4).
            scores: Confidence scores, shape (N,).
            iou_threshold: IoU threshold.

        Returns:
            Indices of kept boxes.
        """
        # Sort by score
        sorted_indices = np.argsort(scores)[::-1]

        keep = []
        while len(sorted_indices) > 0:
            # Keep highest scoring box
            idx = sorted_indices[0]
            keep.append(idx)

            if len(sorted_indices) == 1:
                break

            # Calculate IoU with remaining boxes
            remaining = sorted_indices[1:]
            ious = self._calculate_iou(boxes[idx], boxes[remaining])

            # Filter out boxes with high IoU
            mask = ious <= iou_threshold
            sorted_indices = remaining[mask]

        return keep

    def _calculate_iou(
        self,
        box: np.ndarray,
        boxes: np.ndarray,
    ) -> np.ndarray:
        """Calculate IoU between one box and multiple boxes.

        Args:
            box: Single box, shape (4,).
            boxes: Multiple boxes, shape (N, 4).

        Returns:
            IoU values, shape (N,).
        """
        # Calculate intersection
        x1 = np.maximum(box[0], boxes[:, 0])
        y1 = np.maximum(box[1], boxes[:, 1])
        x2 = np.minimum(box[2], boxes[:, 2])
        y2 = np.minimum(box[3], boxes[:, 3])

        intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)

        # Calculate union
        box_area = (box[2] - box[0]) * (box[3] - box[1])
        boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        union = box_area + boxes_area - intersection

        return intersection / (union + 1e-7)
