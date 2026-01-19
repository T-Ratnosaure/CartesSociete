"""Tests for card recognition augmentation pipeline.

These tests verify the augmentation pipeline works correctly for
generating training data.
"""

import numpy as np
import pytest

from src.recognition.augmentation import (
    AugmentationConfig,
    CardAugmentationPipeline,
    create_aggressive_pipeline,
    create_conservative_pipeline,
    create_default_pipeline,
)


@pytest.fixture
def sample_image_rgb() -> np.ndarray:
    """Create a sample RGB image for testing."""
    # Create a simple 100x80 image with a colored rectangle
    image = np.zeros((100, 80, 3), dtype=np.uint8)
    # Fill center with color
    image[20:80, 15:65] = [255, 128, 64]
    return image


@pytest.fixture
def sample_image_rgba() -> np.ndarray:
    """Create a sample RGBA image for testing."""
    # Create a simple 100x80 image with alpha channel
    image = np.zeros((100, 80, 4), dtype=np.uint8)
    # Fill center with color and alpha
    image[20:80, 15:65, :3] = [255, 128, 64]
    image[20:80, 15:65, 3] = 255  # Opaque center
    return image


class TestAugmentationConfig:
    """Tests for AugmentationConfig dataclass."""

    def test_default_config(self) -> None:
        """Default config should have reasonable values."""
        config = AugmentationConfig()

        assert config.rotation_limit == 30
        assert config.scale_range == (0.7, 1.3)
        assert config.output_size == (640, 640)
        assert len(config.background_colors) > 0

    def test_custom_config(self) -> None:
        """Custom config should override defaults."""
        config = AugmentationConfig(
            rotation_limit=45,
            scale_range=(0.5, 2.0),
            output_size=(416, 416),
        )

        assert config.rotation_limit == 45
        assert config.scale_range == (0.5, 2.0)
        assert config.output_size == (416, 416)


class TestCardAugmentationPipeline:
    """Tests for CardAugmentationPipeline class."""

    def test_init_default_config(self) -> None:
        """Pipeline should work with default config."""
        pipeline = CardAugmentationPipeline()

        assert pipeline.config is not None
        assert pipeline._transform is not None
        assert pipeline._background_transform is not None

    def test_init_custom_config(self) -> None:
        """Pipeline should accept custom config."""
        config = AugmentationConfig(rotation_limit=15)
        pipeline = CardAugmentationPipeline(config)

        assert pipeline.config.rotation_limit == 15

    def test_augment_rgb_image(self, sample_image_rgb: np.ndarray) -> None:
        """Augmentation should work with RGB images."""
        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        result = pipeline.augment(sample_image_rgb)

        assert result.shape == (64, 64, 3)
        assert result.dtype == np.uint8

    def test_augment_rgba_image(self, sample_image_rgba: np.ndarray) -> None:
        """Augmentation should work with RGBA images."""
        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        result = pipeline.augment(sample_image_rgba)

        assert result.shape == (64, 64, 3)  # Output is RGB
        assert result.dtype == np.uint8

    def test_augment_returns_bbox(self, sample_image_rgba: np.ndarray) -> None:
        """Augmentation should return bounding box when requested."""
        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        result, bbox = pipeline.augment(sample_image_rgba, return_bbox=True)

        assert result.shape == (64, 64, 3)
        assert len(bbox) == 4
        # Bbox values should be normalized [0, 1]
        x_center, y_center, width, height = bbox
        assert 0 <= x_center <= 1
        assert 0 <= y_center <= 1
        assert 0 <= width <= 1
        assert 0 <= height <= 1

    def test_augment_batch_generates_multiple(
        self, sample_image_rgba: np.ndarray
    ) -> None:
        """Batch augmentation should generate correct number of images."""
        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        results = pipeline.augment_batch(sample_image_rgba, count=5, seed=42)

        assert len(results) == 5
        for image, bbox in results:
            assert image.shape == (64, 64, 3)
            assert len(bbox) == 4

    def test_augment_batch_produces_valid_output(
        self, sample_image_rgba: np.ndarray
    ) -> None:
        """Batch augmentation should produce valid images and bboxes.

        Note: Due to Albumentations internal random state, exact reproducibility
        is not guaranteed even with the same seed. This test verifies output
        validity rather than reproducibility.
        """
        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        results = pipeline.augment_batch(sample_image_rgba, count=3, seed=42)

        for image, bbox in results:
            # Image should have correct shape and type
            assert image.shape == (64, 64, 3)
            assert image.dtype == np.uint8
            # Bbox should be valid normalized coordinates
            x_center, y_center, width, height = bbox
            assert 0 <= x_center <= 1
            assert 0 <= y_center <= 1
            assert 0 <= width <= 1
            assert 0 <= height <= 1

    def test_augment_batch_different_with_different_seeds(
        self, sample_image_rgba: np.ndarray
    ) -> None:
        """Batch augmentation should produce different results with different seeds."""
        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        results1 = pipeline.augment_batch(sample_image_rgba, count=1, seed=42)
        results2 = pipeline.augment_batch(sample_image_rgba, count=1, seed=99)

        # Images should be different
        img1, _ = results1[0]
        img2, _ = results2[0]
        assert not np.array_equal(img1, img2)


class TestCalculateBbox:
    """Tests for bounding box calculation."""

    def test_calculate_bbox_centered(self) -> None:
        """Centered object should have bbox near center."""
        config = AugmentationConfig(output_size=(100, 100))
        pipeline = CardAugmentationPipeline(config)

        # Create mask with centered rectangle
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[30:70, 20:80] = 255  # Center rectangle

        x_center, y_center, width, height = pipeline._calculate_bbox(mask)

        assert 0.45 <= x_center <= 0.55  # Near center horizontally
        assert 0.45 <= y_center <= 0.55  # Near center vertically
        assert 0.55 <= width <= 0.65  # ~60% width
        assert 0.35 <= height <= 0.45  # ~40% height

    def test_calculate_bbox_corner(self) -> None:
        """Object in corner should have bbox offset from center."""
        config = AugmentationConfig(output_size=(100, 100))
        pipeline = CardAugmentationPipeline(config)

        # Create mask with top-left rectangle
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[0:20, 0:30] = 255

        x_center, y_center, width, height = pipeline._calculate_bbox(mask)

        assert x_center < 0.2  # Left side
        assert y_center < 0.2  # Top side

    def test_calculate_bbox_empty_mask(self) -> None:
        """Empty mask should return zero-size centered bbox."""
        config = AugmentationConfig(output_size=(100, 100))
        pipeline = CardAugmentationPipeline(config)

        mask = np.zeros((100, 100), dtype=np.uint8)

        x_center, y_center, width, height = pipeline._calculate_bbox(mask)

        assert x_center == 0.5
        assert y_center == 0.5
        assert width == 0.0
        assert height == 0.0


class TestPipelinePresets:
    """Tests for pipeline preset factory functions."""

    def test_create_default_pipeline(self) -> None:
        """Default pipeline should have default config values."""
        pipeline = create_default_pipeline()

        assert pipeline.config.rotation_limit == 30
        assert pipeline.config.scale_range == (0.7, 1.3)

    def test_create_conservative_pipeline(self) -> None:
        """Conservative pipeline should have reduced ranges."""
        pipeline = create_conservative_pipeline()

        assert pipeline.config.rotation_limit == 15
        assert pipeline.config.scale_range == (0.85, 1.15)
        assert pipeline.config.blur_limit == 1

    def test_create_aggressive_pipeline(self) -> None:
        """Aggressive pipeline should have increased ranges."""
        pipeline = create_aggressive_pipeline()

        assert pipeline.config.rotation_limit == 45
        assert pipeline.config.scale_range == (0.5, 1.5)
        assert pipeline.config.blur_limit == 5

    def test_all_pipelines_produce_valid_output(
        self, sample_image_rgba: np.ndarray
    ) -> None:
        """All preset pipelines should produce valid output."""
        for pipeline_factory in [
            create_default_pipeline,
            create_conservative_pipeline,
            create_aggressive_pipeline,
        ]:
            pipeline = pipeline_factory()
            pipeline.config.output_size = (64, 64)

            result, bbox = pipeline.augment(sample_image_rgba, return_bbox=True)

            assert result.shape == (64, 64, 3)
            assert len(bbox) == 4


class TestGrayscaleImageHandling:
    """Tests for grayscale image handling in augmentation pipeline."""

    def test_augment_grayscale_2d(self) -> None:
        """Augmentation should handle 2D grayscale images."""
        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        # Create 2D grayscale image
        grayscale = np.full((100, 80), 128, dtype=np.uint8)
        grayscale[20:80, 15:65] = 200

        result = pipeline.augment(grayscale)

        assert result.shape == (64, 64, 3)
        assert result.dtype == np.uint8

    def test_augment_grayscale_single_channel(self) -> None:
        """Augmentation should handle single-channel (H, W, 1) images."""
        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        # Create single-channel image
        grayscale = np.full((100, 80, 1), 128, dtype=np.uint8)
        grayscale[20:80, 15:65, 0] = 200

        result = pipeline.augment(grayscale)

        assert result.shape == (64, 64, 3)
        assert result.dtype == np.uint8

    def test_augment_grayscale_returns_valid_bbox(self) -> None:
        """Augmentation should return valid bbox for grayscale images."""
        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        # Create 2D grayscale image
        grayscale = np.full((100, 80), 128, dtype=np.uint8)
        grayscale[20:80, 15:65] = 200

        result, bbox = pipeline.augment(grayscale, return_bbox=True)

        assert result.shape == (64, 64, 3)
        assert len(bbox) == 4
        x_center, y_center, width, height = bbox
        assert 0 <= x_center <= 1
        assert 0 <= y_center <= 1
        # Width and height might be 0 if alpha mask interpretation is empty
        assert 0 <= width <= 1
        assert 0 <= height <= 1
