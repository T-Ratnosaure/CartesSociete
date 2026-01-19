"""Configuration for card recognition model training and inference.

This module defines configuration dataclasses for YOLOv8 training,
export, and inference settings. All configurations are designed for
mobile deployment of a 159-class card detector.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class ModelConfig:
    """Configuration for YOLOv8 model selection.

    Attributes:
        variant: YOLOv8 model variant (n=nano, s=small, m=medium).
        pretrained_weights: Path to pretrained weights or 'coco' for COCO.
        num_classes: Number of card classes to detect.
        image_size: Input image size (square).
    """

    variant: Literal["n", "s", "m"] = "s"
    pretrained_weights: str = "yolov8s.pt"
    num_classes: int = 159
    image_size: int = 640

    @property
    def model_name(self) -> str:
        """Get full model name with variant."""
        return f"yolov8{self.variant}"


@dataclass
class TrainingConfig:
    """Configuration for YOLOv8 training.

    Attributes:
        epochs: Maximum number of training epochs.
        batch_size: Training batch size.
        patience: Early stopping patience (epochs without improvement).
        optimizer: Optimizer name (SGD, Adam, AdamW).
        learning_rate: Initial learning rate.
        learning_rate_final: Final learning rate factor (lr * lrf).
        momentum: SGD momentum or Adam beta1.
        weight_decay: L2 regularization weight decay.
        warmup_epochs: Number of warmup epochs.
        warmup_momentum: Warmup momentum.
        warmup_bias_lr: Warmup bias learning rate.
        device: Training device ('cuda', 'cpu', or device id).
        workers: Number of data loader workers.
        amp: Enable automatic mixed precision training.
        cache: Cache images ('ram', 'disk', or False).
        resume: Resume training from checkpoint.
        freeze_backbone_epochs: Epochs to freeze backbone (0 to disable).
    """

    epochs: int = 100
    batch_size: int = 16
    patience: int = 20
    optimizer: Literal["SGD", "Adam", "AdamW"] = "AdamW"
    learning_rate: float = 0.001
    learning_rate_final: float = 0.01
    momentum: float = 0.937
    weight_decay: float = 0.0005
    warmup_epochs: float = 3.0
    warmup_momentum: float = 0.8
    warmup_bias_lr: float = 0.1
    device: str = ""  # Empty string = auto-detect
    workers: int = 8
    amp: bool = True
    cache: bool | str = False
    resume: bool = False
    freeze_backbone_epochs: int = 10


@dataclass
class AugmentationTrainingConfig:
    """YOLOv8 training-time augmentation configuration.

    Note: Heavy augmentations are already applied in Phase 1 synthetic
    data generation. These are lighter augmentations applied during training.

    Attributes:
        hsv_h: HSV hue augmentation (fraction).
        hsv_s: HSV saturation augmentation (fraction).
        hsv_v: HSV value augmentation (fraction).
        degrees: Rotation degrees (+/- this value).
        translate: Translation fraction.
        scale: Scale augmentation gain.
        shear: Shear degrees (+/- this value).
        perspective: Perspective augmentation (0-0.001).
        flipud: Vertical flip probability (0 for cards).
        fliplr: Horizontal flip probability (0 for cards).
        mosaic: Mosaic augmentation probability.
        mixup: MixUp augmentation probability.
        copy_paste: Copy-paste augmentation probability.
    """

    hsv_h: float = 0.015
    hsv_s: float = 0.7
    hsv_v: float = 0.4
    degrees: float = 0.0  # Already applied in Phase 1
    translate: float = 0.1
    scale: float = 0.5
    shear: float = 0.0
    perspective: float = 0.0
    flipud: float = 0.0  # Cards should not be flipped
    fliplr: float = 0.0  # Cards should not be flipped
    mosaic: float = 0.5
    mixup: float = 0.1
    copy_paste: float = 0.0


@dataclass
class ExportConfig:
    """Configuration for ONNX model export.

    Attributes:
        format: Export format (onnx, torchscript, etc.).
        image_size: Export image size.
        opset: ONNX opset version.
        simplify: Simplify ONNX model graph.
        dynamic: Enable dynamic input shapes.
        half: Export as FP16 (half precision).
        int8: Export as INT8 (quantized).
        nms: Include NMS in exported model.
        batch_size: Export batch size (1 for mobile).
    """

    format: Literal["onnx", "torchscript", "tflite", "coreml"] = "onnx"
    image_size: int = 640
    opset: int = 17
    simplify: bool = True
    dynamic: bool = True
    half: bool = False
    int8: bool = False
    nms: bool = False
    batch_size: int = 1


@dataclass
class InferenceConfig:
    """Configuration for model inference.

    Attributes:
        confidence_threshold: Minimum confidence for detections.
        iou_threshold: IoU threshold for NMS.
        max_detections: Maximum detections per image.
        device: Inference device ('cuda', 'cpu', or device id).
        half: Use FP16 inference.
        verbose: Enable verbose output.
    """

    confidence_threshold: float = 0.25
    iou_threshold: float = 0.45
    max_detections: int = 300
    device: str = ""  # Empty string = auto-detect
    half: bool = False
    verbose: bool = False


@dataclass
class CardDetectorConfig:
    """Complete configuration for card detector training and inference.

    This is the main configuration class that combines all sub-configurations.

    Attributes:
        model: Model architecture configuration.
        training: Training hyperparameters.
        augmentation: Training-time augmentation settings.
        export: ONNX export settings.
        inference: Inference settings.
        data_yaml: Path to YOLO data.yaml file.
        output_dir: Directory for training outputs.
        project_name: Project name for logging.
        experiment_name: Experiment name for logging.
    """

    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    augmentation: AugmentationTrainingConfig = field(
        default_factory=AugmentationTrainingConfig
    )
    export: ExportConfig = field(default_factory=ExportConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    data_yaml: Path | None = None
    output_dir: Path = field(default_factory=lambda: Path("runs/detect"))
    project_name: str = "card_detector"
    experiment_name: str = "train"


def create_mobile_optimized_config() -> CardDetectorConfig:
    """Create configuration optimized for mobile deployment.

    Returns smaller model variant and INT8 quantization for
    optimal mobile inference performance.

    Returns:
        CardDetectorConfig optimized for mobile.
    """
    config = CardDetectorConfig()

    # Use smaller model for mobile
    config.model = ModelConfig(
        variant="n",
        pretrained_weights="yolov8n.pt",
        num_classes=159,
        image_size=640,
    )

    # INT8 quantization for mobile
    config.export = ExportConfig(
        format="onnx",
        image_size=640,
        simplify=True,
        dynamic=False,  # Fixed size for mobile
        int8=True,
        batch_size=1,
    )

    return config


def create_accuracy_focused_config() -> CardDetectorConfig:
    """Create configuration focused on maximum accuracy.

    Returns larger model variant and no quantization for
    maximum detection accuracy.

    Returns:
        CardDetectorConfig optimized for accuracy.
    """
    config = CardDetectorConfig()

    # Use larger model for accuracy
    config.model = ModelConfig(
        variant="m",
        pretrained_weights="yolov8m.pt",
        num_classes=159,
        image_size=640,
    )

    # More training for accuracy
    config.training = TrainingConfig(
        epochs=150,
        batch_size=8,  # Larger model needs smaller batch
        patience=30,
        learning_rate=0.0005,
    )

    return config


def create_balanced_config() -> CardDetectorConfig:
    """Create balanced configuration for accuracy and speed.

    This is the default configuration, suitable for most use cases.

    Returns:
        CardDetectorConfig with balanced settings.
    """
    return CardDetectorConfig()
