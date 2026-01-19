"""Tests for card recognition configuration module."""

from pathlib import Path

from src.recognition.config import (
    AugmentationTrainingConfig,
    CardDetectorConfig,
    ExportConfig,
    InferenceConfig,
    ModelConfig,
    TrainingConfig,
    create_accuracy_focused_config,
    create_balanced_config,
    create_mobile_optimized_config,
)


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default model configuration values."""
        config = ModelConfig()

        assert config.variant == "s"
        assert config.pretrained_weights == "yolov8s.pt"
        assert config.num_classes == 159
        assert config.image_size == 640

    def test_model_name_property(self) -> None:
        """Test model_name property generation."""
        config_n = ModelConfig(variant="n")
        config_s = ModelConfig(variant="s")
        config_m = ModelConfig(variant="m")

        assert config_n.model_name == "yolov8n"
        assert config_s.model_name == "yolov8s"
        assert config_m.model_name == "yolov8m"

    def test_custom_values(self) -> None:
        """Test custom model configuration values."""
        config = ModelConfig(
            variant="m",
            pretrained_weights="custom.pt",
            num_classes=100,
            image_size=416,
        )

        assert config.variant == "m"
        assert config.pretrained_weights == "custom.pt"
        assert config.num_classes == 100
        assert config.image_size == 416


class TestTrainingConfig:
    """Tests for TrainingConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default training configuration values."""
        config = TrainingConfig()

        assert config.epochs == 100
        assert config.batch_size == 16
        assert config.patience == 20
        assert config.optimizer == "AdamW"
        assert config.learning_rate == 0.001
        assert config.learning_rate_final == 0.01
        assert config.momentum == 0.937
        assert config.weight_decay == 0.0005
        assert config.warmup_epochs == 3.0
        assert config.workers == 8
        assert config.amp is True
        assert config.cache is False
        assert config.resume is False
        assert config.freeze_backbone_epochs == 10

    def test_custom_values(self) -> None:
        """Test custom training configuration values."""
        config = TrainingConfig(
            epochs=50,
            batch_size=32,
            learning_rate=0.0005,
            device="cuda:1",
        )

        assert config.epochs == 50
        assert config.batch_size == 32
        assert config.learning_rate == 0.0005
        assert config.device == "cuda:1"


class TestAugmentationTrainingConfig:
    """Tests for AugmentationTrainingConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default augmentation configuration values."""
        config = AugmentationTrainingConfig()

        # Color augmentation
        assert config.hsv_h == 0.015
        assert config.hsv_s == 0.7
        assert config.hsv_v == 0.4

        # Geometric (minimal since Phase 1 handles heavy augmentation)
        assert config.degrees == 0.0
        assert config.translate == 0.1
        assert config.scale == 0.5

        # Flip should be disabled for cards
        assert config.flipud == 0.0
        assert config.fliplr == 0.0

        # Composite augmentation
        assert config.mosaic == 0.5
        assert config.mixup == 0.1

    def test_no_flip_for_cards(self) -> None:
        """Test that flip augmentations are disabled by default for cards."""
        config = AugmentationTrainingConfig()

        # Cards should never be flipped as orientation matters
        assert config.flipud == 0.0
        assert config.fliplr == 0.0


class TestExportConfig:
    """Tests for ExportConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default export configuration values."""
        config = ExportConfig()

        assert config.format == "onnx"
        assert config.image_size == 640
        assert config.opset == 17
        assert config.simplify is True
        assert config.dynamic is True
        assert config.half is False
        assert config.int8 is False
        assert config.nms is False
        assert config.batch_size == 1

    def test_mobile_export_config(self) -> None:
        """Test mobile-optimized export configuration."""
        config = ExportConfig(
            int8=True,
            dynamic=False,  # Fixed size for mobile
            batch_size=1,
        )

        assert config.int8 is True
        assert config.dynamic is False
        assert config.batch_size == 1


class TestInferenceConfig:
    """Tests for InferenceConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default inference configuration values."""
        config = InferenceConfig()

        assert config.confidence_threshold == 0.25
        assert config.iou_threshold == 0.45
        assert config.max_detections == 300
        assert config.device == ""
        assert config.half is False
        assert config.verbose is False

    def test_custom_thresholds(self) -> None:
        """Test custom confidence and IoU thresholds."""
        config = InferenceConfig(
            confidence_threshold=0.5,
            iou_threshold=0.3,
        )

        assert config.confidence_threshold == 0.5
        assert config.iou_threshold == 0.3


class TestCardDetectorConfig:
    """Tests for CardDetectorConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default full configuration."""
        config = CardDetectorConfig()

        assert isinstance(config.model, ModelConfig)
        assert isinstance(config.training, TrainingConfig)
        assert isinstance(config.augmentation, AugmentationTrainingConfig)
        assert isinstance(config.export, ExportConfig)
        assert isinstance(config.inference, InferenceConfig)
        assert config.data_yaml is None
        assert config.output_dir == Path("runs/detect")
        assert config.project_name == "card_detector"
        assert config.experiment_name == "train"

    def test_nested_config_access(self) -> None:
        """Test accessing nested configuration values."""
        config = CardDetectorConfig()

        assert config.model.variant == "s"
        assert config.training.epochs == 100
        assert config.augmentation.mosaic == 0.5
        assert config.export.format == "onnx"
        assert config.inference.confidence_threshold == 0.25


class TestConfigFactoryFunctions:
    """Tests for configuration factory functions."""

    def test_mobile_optimized_config(self) -> None:
        """Test mobile-optimized configuration preset."""
        config = create_mobile_optimized_config()

        # Should use nano model for mobile
        assert config.model.variant == "n"
        assert config.model.pretrained_weights == "yolov8n.pt"

        # Should use INT8 quantization
        assert config.export.int8 is True
        assert config.export.dynamic is False  # Fixed size for mobile
        assert config.export.batch_size == 1

    def test_accuracy_focused_config(self) -> None:
        """Test accuracy-focused configuration preset."""
        config = create_accuracy_focused_config()

        # Should use medium model for accuracy
        assert config.model.variant == "m"
        assert config.model.pretrained_weights == "yolov8m.pt"

        # Should have more training epochs
        assert config.training.epochs == 150
        assert config.training.patience == 30
        assert config.training.learning_rate == 0.0005

    def test_balanced_config(self) -> None:
        """Test balanced configuration preset (default)."""
        config = create_balanced_config()

        # Should be same as default
        default = CardDetectorConfig()

        assert config.model.variant == default.model.variant
        assert config.training.epochs == default.training.epochs
        assert config.export.format == default.export.format

    def test_config_immutability_not_enforced(self) -> None:
        """Test that configs can be modified after creation."""
        config = create_balanced_config()

        # Should be able to modify after creation
        config.model.variant = "l"
        assert config.model.variant == "l"

        config.training.epochs = 200
        assert config.training.epochs == 200
