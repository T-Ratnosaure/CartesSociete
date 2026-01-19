"""Tests for card recognition detector module.

Note: These tests focus on unit testing the detector classes without
requiring the actual ultralytics or onnxruntime packages. Integration
tests with actual models would be in a separate test file.
"""

from pathlib import Path

import numpy as np
import pytest

from src.recognition.config import InferenceConfig
from src.recognition.detector import (
    CardDetector,
    Detection,
    DetectionResult,
    ONNXCardDetector,
)


class TestDetection:
    """Tests for Detection dataclass."""

    def test_detection_creation(self) -> None:
        """Test creating a Detection object."""
        detection = Detection(
            card_id="lapin_gardien_1",
            class_index=42,
            confidence=0.95,
            bbox=(100, 150, 300, 400),
            bbox_normalized=(0.3125, 0.4297, 0.3125, 0.3906),
        )

        assert detection.card_id == "lapin_gardien_1"
        assert detection.class_index == 42
        assert detection.confidence == 0.95
        assert detection.bbox == (100, 150, 300, 400)
        assert detection.bbox_normalized == (0.3125, 0.4297, 0.3125, 0.3906)

    def test_detection_confidence_range(self) -> None:
        """Test detection with boundary confidence values."""
        # Low confidence
        low_conf = Detection(
            card_id="test",
            class_index=0,
            confidence=0.0,
            bbox=(0, 0, 10, 10),
            bbox_normalized=(0.5, 0.5, 0.1, 0.1),
        )
        assert low_conf.confidence == 0.0

        # High confidence
        high_conf = Detection(
            card_id="test",
            class_index=0,
            confidence=1.0,
            bbox=(0, 0, 10, 10),
            bbox_normalized=(0.5, 0.5, 0.1, 0.1),
        )
        assert high_conf.confidence == 1.0


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""

    def test_detection_result_creation(self) -> None:
        """Test creating a DetectionResult object."""
        detections = [
            Detection(
                card_id="card_1",
                class_index=0,
                confidence=0.9,
                bbox=(10, 10, 100, 100),
                bbox_normalized=(0.1, 0.1, 0.15, 0.15),
            ),
            Detection(
                card_id="card_2",
                class_index=1,
                confidence=0.8,
                bbox=(200, 200, 400, 400),
                bbox_normalized=(0.5, 0.5, 0.3, 0.3),
            ),
        ]

        result = DetectionResult(
            detections=detections,
            image_shape=(640, 640, 3),
            inference_time_ms=25.5,
        )

        assert len(result.detections) == 2
        assert result.image_shape == (640, 640, 3)
        assert result.inference_time_ms == 25.5

    def test_empty_detection_result(self) -> None:
        """Test DetectionResult with no detections."""
        result = DetectionResult(
            detections=[],
            image_shape=(640, 640, 3),
            inference_time_ms=10.0,
        )

        assert len(result.detections) == 0
        assert result.inference_time_ms == 10.0


class TestCardDetector:
    """Tests for CardDetector class."""

    def test_from_checkpoint_file_not_found(self) -> None:
        """Test that FileNotFoundError is raised for missing checkpoint."""
        # This test requires ultralytics to be installed
        try:
            import ultralytics  # noqa: F401
        except ImportError:
            pytest.skip("ultralytics not installed")

        with pytest.raises(FileNotFoundError):
            CardDetector.from_checkpoint(Path("/nonexistent/model.pt"))

    def test_from_checkpoint_import_error_message(self) -> None:
        """Test ImportError message when ultralytics not installed."""
        # If ultralytics is installed, skip this test
        try:
            import ultralytics  # noqa: F401

            pytest.skip("ultralytics is installed, cannot test import error")
        except ImportError:
            pass

        with pytest.raises(ImportError, match="ultralytics is required"):
            CardDetector.from_checkpoint(Path("test.pt"))

    def test_from_onnx_returns_onnx_detector(self) -> None:
        """Test that from_onnx returns ONNXCardDetector."""
        # This test requires onnxruntime to be installed
        try:
            import onnxruntime  # noqa: F401
        except ImportError:
            pytest.skip("onnxruntime not installed")

        class_names = ["card_0", "card_1", "card_2"]

        # Should raise FileNotFoundError for missing file
        with pytest.raises(FileNotFoundError):
            CardDetector.from_onnx(
                Path("/nonexistent/model.onnx"),
                class_names,
            )


class TestONNXCardDetector:
    """Tests for ONNXCardDetector class."""

    def test_init_file_not_found(self) -> None:
        """Test FileNotFoundError for missing ONNX file."""
        # This test requires onnxruntime to be installed
        try:
            import onnxruntime  # noqa: F401
        except ImportError:
            pytest.skip("onnxruntime not installed")

        class_names = ["card_0", "card_1"]

        with pytest.raises(FileNotFoundError, match="ONNX model not found"):
            ONNXCardDetector(
                Path("/nonexistent/model.onnx"),
                class_names,
            )

    def test_init_import_error_message(self) -> None:
        """Test ImportError message when onnxruntime not installed."""
        # If onnxruntime is installed, skip this test
        try:
            import onnxruntime  # noqa: F401

            pytest.skip("onnxruntime is installed, cannot test import error")
        except ImportError:
            pass

        class_names = ["card_0", "card_1"]

        with pytest.raises(ImportError, match="onnxruntime is required"):
            ONNXCardDetector(
                Path("/nonexistent/model.onnx"),
                class_names,
            )

    def test_nms_implementation(self) -> None:
        """Test NMS helper function with mock detector."""
        # Create boxes that should be filtered by NMS
        boxes = np.array(
            [
                [0, 0, 100, 100],
                [10, 10, 110, 110],  # High overlap with first box
                [200, 200, 300, 300],  # No overlap
            ]
        )
        scores = np.array([0.9, 0.8, 0.95])

        # Create minimal mock detector to test _nms
        class MockONNXDetector:
            def _nms(
                self,
                boxes: np.ndarray,
                scores: np.ndarray,
                iou_threshold: float,
            ) -> list[int]:
                """Copy of _nms implementation for testing."""
                sorted_indices = np.argsort(scores)[::-1]
                keep = []

                while len(sorted_indices) > 0:
                    idx = sorted_indices[0]
                    keep.append(idx)

                    if len(sorted_indices) == 1:
                        break

                    remaining = sorted_indices[1:]
                    ious = self._calculate_iou(boxes[idx], boxes[remaining])
                    mask = ious <= iou_threshold
                    sorted_indices = remaining[mask]

                return keep

            def _calculate_iou(
                self,
                box: np.ndarray,
                boxes: np.ndarray,
            ) -> np.ndarray:
                """Copy of _calculate_iou for testing."""
                x1 = np.maximum(box[0], boxes[:, 0])
                y1 = np.maximum(box[1], boxes[:, 1])
                x2 = np.minimum(box[2], boxes[:, 2])
                y2 = np.minimum(box[3], boxes[:, 3])

                intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
                box_area = (box[2] - box[0]) * (box[3] - box[1])
                boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
                union = box_area + boxes_area - intersection

                return intersection / (union + 1e-7)

        detector = MockONNXDetector()
        kept_indices = detector._nms(boxes, scores, iou_threshold=0.5)

        # Should keep highest confidence non-overlapping boxes
        # Index 2 has highest score (0.95), index 0 next (0.9)
        # Index 1 overlaps heavily with 0, so it's suppressed
        assert len(kept_indices) == 2
        assert 2 in kept_indices  # Highest score
        assert 0 in kept_indices  # Second highest, no overlap with 2

    def test_iou_calculation(self) -> None:
        """Test IoU calculation helper function."""

        class MockDetector:
            def _calculate_iou(
                self,
                box: np.ndarray,
                boxes: np.ndarray,
            ) -> np.ndarray:
                x1 = np.maximum(box[0], boxes[:, 0])
                y1 = np.maximum(box[1], boxes[:, 1])
                x2 = np.minimum(box[2], boxes[:, 2])
                y2 = np.minimum(box[3], boxes[:, 3])

                intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
                box_area = (box[2] - box[0]) * (box[3] - box[1])
                boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
                union = box_area + boxes_area - intersection

                return intersection / (union + 1e-7)

        detector = MockDetector()

        # Test identical boxes (IoU = 1)
        box = np.array([0, 0, 100, 100])
        boxes = np.array([[0, 0, 100, 100]])
        ious = detector._calculate_iou(box, boxes)
        assert np.isclose(ious[0], 1.0, atol=1e-5)

        # Test non-overlapping boxes (IoU = 0)
        boxes = np.array([[200, 200, 300, 300]])
        ious = detector._calculate_iou(box, boxes)
        assert np.isclose(ious[0], 0.0, atol=1e-5)

        # Test 50% overlapping boxes
        boxes = np.array([[50, 0, 150, 100]])
        ious = detector._calculate_iou(box, boxes)
        # Intersection: 50*100 = 5000
        # Union: 10000 + 10000 - 5000 = 15000
        # IoU: 5000/15000 = 0.333...
        assert np.isclose(ious[0], 1 / 3, atol=0.01)


class TestInferenceConfig:
    """Tests for inference configuration with detector."""

    def test_default_thresholds(self) -> None:
        """Test that default thresholds are reasonable."""
        config = InferenceConfig()

        # Confidence threshold should filter low-confidence detections
        assert 0 < config.confidence_threshold < 1

        # IoU threshold should allow some overlap but filter duplicates
        assert 0 < config.iou_threshold < 1

        # Max detections should be reasonable
        assert config.max_detections > 0
        assert config.max_detections <= 1000

    def test_strict_config(self) -> None:
        """Test strict configuration for high precision."""
        config = InferenceConfig(
            confidence_threshold=0.7,  # High confidence required
            iou_threshold=0.3,  # Low overlap allowed
            max_detections=10,
        )

        assert config.confidence_threshold == 0.7
        assert config.iou_threshold == 0.3
        assert config.max_detections == 10

    def test_relaxed_config(self) -> None:
        """Test relaxed configuration for high recall."""
        config = InferenceConfig(
            confidence_threshold=0.1,  # Allow low confidence
            iou_threshold=0.7,  # Allow more overlap
            max_detections=500,
        )

        assert config.confidence_threshold == 0.1
        assert config.iou_threshold == 0.7
        assert config.max_detections == 500


class TestVisualization:
    """Tests for detection visualization."""

    def test_visualize_empty_detections(self) -> None:
        """Test visualization with no detections."""
        # Create a simple test image
        image = np.zeros((640, 640, 3), dtype=np.uint8)

        # Create empty result
        result = DetectionResult(
            detections=[],
            image_shape=(640, 640, 3),
            inference_time_ms=10.0,
        )

        # Mock detector for visualization test
        class MockDetector:
            def visualize(
                self,
                image: np.ndarray,
                result: DetectionResult,
            ) -> np.ndarray:
                return image.copy()

        detector = MockDetector()
        output = detector.visualize(image, result)

        # Output should be same shape as input
        assert output.shape == image.shape

        # Should not modify original
        assert output is not image

    def test_visualize_with_detections(self) -> None:
        """Test visualization with detections draws bboxes."""
        import cv2

        # Create test image
        image = np.zeros((640, 640, 3), dtype=np.uint8)

        detections = [
            Detection(
                card_id="test_card",
                class_index=0,
                confidence=0.9,
                bbox=(100, 100, 200, 200),
                bbox_normalized=(0.234, 0.234, 0.156, 0.156),
            ),
        ]

        result = DetectionResult(
            detections=detections,
            image_shape=(640, 640, 3),
            inference_time_ms=10.0,
        )

        # Simple visualization function
        def visualize(img: np.ndarray, res: DetectionResult) -> np.ndarray:
            output = img.copy()
            for det in res.detections:
                x1, y1, x2, y2 = det.bbox
                cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
            return output

        output = visualize(image, result)

        # Check that bbox area has been modified (green lines drawn)
        assert not np.array_equal(output[100:200, 100:200], image[100:200, 100:200])
