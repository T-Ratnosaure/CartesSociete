"""Card recognition module for CartesSociete.

This module provides tools for generating training data and recognizing
playing cards using computer vision techniques.

Submodules:
    augmentation: Image augmentation pipeline for training data generation
    dataset_generator: Synthetic dataset generation in YOLO format
    config: Configuration for model training and inference
    detector: YOLOv8 and ONNX inference wrappers
"""

from .augmentation import (
    AugmentationConfig,
    CardAugmentationPipeline,
)
from .config import (
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
from .dataset_generator import (
    DatasetStats,
    SyntheticDatasetGenerator,
)
from .detector import (
    CardDetector,
    Detection,
    DetectionResult,
    ONNXCardDetector,
)

__all__ = [
    # Augmentation (Phase 1)
    "AugmentationConfig",
    "CardAugmentationPipeline",
    # Dataset Generation (Phase 1)
    "DatasetStats",
    "SyntheticDatasetGenerator",
    # Configuration (Phase 2)
    "AugmentationTrainingConfig",
    "CardDetectorConfig",
    "ExportConfig",
    "InferenceConfig",
    "ModelConfig",
    "TrainingConfig",
    "create_accuracy_focused_config",
    "create_balanced_config",
    "create_mobile_optimized_config",
    # Detection (Phase 2)
    "CardDetector",
    "Detection",
    "DetectionResult",
    "ONNXCardDetector",
]
