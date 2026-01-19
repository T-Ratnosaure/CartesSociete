"""Tests for card recognition dataset generator.

These tests verify the dataset generator correctly produces YOLO-format
training data.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
import yaml

from src.cards.models import (
    Card,
    CardClass,
    CardType,
    ClassAbilities,
    Family,
    FamilyAbilities,
)
from src.recognition.augmentation import AugmentationConfig, CardAugmentationPipeline
from src.recognition.dataset_generator import (
    DatasetStats,
    SyntheticDatasetGenerator,
    create_generator,
)


@pytest.fixture
def mock_card() -> Card:
    """Create a mock card for testing."""
    return Card(
        id="test_card_1",
        name="Test Card",
        card_type=CardType.CREATURE,
        cost=3,
        level=1,
        family=Family.LAPIN,
        card_class=CardClass.COMBATTANT,
        family_abilities=FamilyAbilities(),
        class_abilities=ClassAbilities(),
        bonus_text=None,
        health=5,
        attack=3,
        image_path="test_family/test_card.png",
    )


@pytest.fixture
def mock_repository(mock_card: Card) -> MagicMock:
    """Create a mock card repository."""
    repo = MagicMock()
    repo.get_all.return_value = [mock_card]
    repo.get.return_value = mock_card
    return repo


@pytest.fixture
def sample_image() -> np.ndarray:
    """Create a sample image for testing."""
    # Create a simple 100x80 RGBA image
    image = np.zeros((100, 80, 4), dtype=np.uint8)
    image[20:80, 15:65, :3] = [255, 128, 64]
    image[20:80, 15:65, 3] = 255
    return image


class TestDatasetStats:
    """Tests for DatasetStats dataclass."""

    def test_default_values(self) -> None:
        """DatasetStats should have sensible defaults."""
        stats = DatasetStats()

        assert stats.total_cards == 0
        assert stats.cards_processed == 0
        assert stats.cards_skipped == 0
        assert stats.images_generated == 0
        assert stats.train_images == 0
        assert stats.val_images == 0
        assert stats.skipped_cards == []

    def test_custom_values(self) -> None:
        """DatasetStats should accept custom values."""
        stats = DatasetStats(
            total_cards=100,
            cards_processed=90,
            cards_skipped=10,
            skipped_cards=["card_a", "card_b"],
        )

        assert stats.total_cards == 100
        assert stats.cards_skipped == 10
        assert len(stats.skipped_cards) == 2


class TestSyntheticDatasetGenerator:
    """Tests for SyntheticDatasetGenerator class."""

    def test_init_defaults(self) -> None:
        """Generator should initialize with defaults."""
        generator = SyntheticDatasetGenerator()

        assert generator.card_repository is not None
        assert generator.images_dir is None
        assert generator.output_dir is None
        assert generator.augmentation_pipeline is not None

    def test_init_with_params(self, mock_repository: MagicMock) -> None:
        """Generator should accept custom parameters."""
        images_dir = Path("/test/images")
        output_dir = Path("/test/output")
        pipeline = CardAugmentationPipeline()

        generator = SyntheticDatasetGenerator(
            card_repository=mock_repository,
            images_dir=images_dir,
            output_dir=output_dir,
            augmentation_pipeline=pipeline,
        )

        assert generator.card_repository == mock_repository
        assert generator.images_dir == images_dir
        assert generator.output_dir == output_dir

    def test_build_class_map(self, mock_repository: MagicMock) -> None:
        """Class map should assign indices to card IDs."""
        generator = SyntheticDatasetGenerator(card_repository=mock_repository)

        class_map = generator._build_class_map()

        assert "test_card_1" in class_map
        assert class_map["test_card_1"] == 0

    def test_build_class_map_sorted(self, mock_repository: MagicMock) -> None:
        """Class map should be sorted alphabetically."""
        card_a = MagicMock(id="alpha_card")
        card_b = MagicMock(id="beta_card")
        card_c = MagicMock(id="gamma_card")
        mock_repository.get_all.return_value = [card_c, card_a, card_b]

        generator = SyntheticDatasetGenerator(card_repository=mock_repository)
        class_map = generator._build_class_map()

        assert class_map["alpha_card"] == 0
        assert class_map["beta_card"] == 1
        assert class_map["gamma_card"] == 2

    def test_generate_requires_images_dir(self, mock_repository: MagicMock) -> None:
        """Generate should raise if images_dir not set."""
        generator = SyntheticDatasetGenerator(
            card_repository=mock_repository,
            output_dir=Path("/test/output"),
        )

        with pytest.raises(ValueError, match="images_dir must be set"):
            generator.generate()

    def test_generate_requires_output_dir(self, mock_repository: MagicMock) -> None:
        """Generate should raise if output_dir not set."""
        generator = SyntheticDatasetGenerator(
            card_repository=mock_repository,
            images_dir=Path("/test/images"),
        )

        with pytest.raises(ValueError, match="output_dir must be set"):
            generator.generate()

    def test_find_image_path_exact_match(self) -> None:
        """Should find image with exact path match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image file
            images_dir = Path(tmpdir)
            family_dir = images_dir / "test_family"
            family_dir.mkdir()
            image_path = family_dir / "test_card.png"
            image_path.touch()

            generator = SyntheticDatasetGenerator(images_dir=images_dir)

            result = generator._find_image_path("test_family/test_card.png")

            assert result is not None
            assert result.exists()

    def test_find_image_path_not_found(self) -> None:
        """Should return None for missing image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = SyntheticDatasetGenerator(images_dir=Path(tmpdir))

            result = generator._find_image_path("nonexistent/card.png")

            assert result is None


class TestDatasetGeneration:
    """Integration tests for full dataset generation."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as images_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                yield Path(images_dir), Path(output_dir)

    def test_generate_creates_output_structure(
        self,
        mock_repository: MagicMock,
        temp_dirs: tuple[Path, Path],
        sample_image: np.ndarray,
    ) -> None:
        """Generate should create proper directory structure."""
        images_dir, output_dir = temp_dirs

        # Create test image
        import cv2

        family_dir = images_dir / "test_family"
        family_dir.mkdir()
        image_path = family_dir / "test_card.png"
        cv2.imwrite(str(image_path), sample_image)

        # Configure small augmentation for speed
        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        generator = SyntheticDatasetGenerator(
            card_repository=mock_repository,
            images_dir=images_dir,
            output_dir=output_dir,
            augmentation_pipeline=pipeline,
        )

        generator.generate(
            augmentations_per_card=5,
            val_split=0.2,
            seed=42,
        )

        # Check structure created
        assert (output_dir / "images" / "train").exists()
        assert (output_dir / "images" / "val").exists()
        assert (output_dir / "labels" / "train").exists()
        assert (output_dir / "labels" / "val").exists()
        assert (output_dir / "data.yaml").exists()

    def test_generate_creates_data_yaml(
        self,
        mock_repository: MagicMock,
        temp_dirs: tuple[Path, Path],
        sample_image: np.ndarray,
    ) -> None:
        """Generate should create valid data.yaml."""
        images_dir, output_dir = temp_dirs

        # Create test image
        import cv2

        family_dir = images_dir / "test_family"
        family_dir.mkdir()
        image_path = family_dir / "test_card.png"
        cv2.imwrite(str(image_path), sample_image)

        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        generator = SyntheticDatasetGenerator(
            card_repository=mock_repository,
            images_dir=images_dir,
            output_dir=output_dir,
            augmentation_pipeline=pipeline,
        )

        generator.generate(augmentations_per_card=2, seed=42)

        # Check data.yaml content
        with open(output_dir / "data.yaml") as f:
            data = yaml.safe_load(f)

        assert "nc" in data
        assert data["nc"] == 1  # One card
        assert "names" in data
        assert "test_card_1" in data["names"]
        assert data["train"] == "images/train"
        assert data["val"] == "images/val"

    def test_generate_returns_correct_stats(
        self,
        mock_repository: MagicMock,
        temp_dirs: tuple[Path, Path],
        sample_image: np.ndarray,
    ) -> None:
        """Generate should return accurate statistics."""
        images_dir, output_dir = temp_dirs

        # Create test image
        import cv2

        family_dir = images_dir / "test_family"
        family_dir.mkdir()
        image_path = family_dir / "test_card.png"
        cv2.imwrite(str(image_path), sample_image)

        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        generator = SyntheticDatasetGenerator(
            card_repository=mock_repository,
            images_dir=images_dir,
            output_dir=output_dir,
            augmentation_pipeline=pipeline,
        )

        stats = generator.generate(
            augmentations_per_card=10,
            val_split=0.2,
            seed=42,
        )

        assert stats.total_cards == 1
        assert stats.cards_processed == 1
        assert stats.cards_skipped == 0
        assert stats.train_images == 8  # 80% of 10
        assert stats.val_images == 2  # 20% of 10
        assert stats.images_generated == 10

    def test_generate_skips_missing_images(
        self,
        mock_repository: MagicMock,
        temp_dirs: tuple[Path, Path],
    ) -> None:
        """Generate should skip cards with missing images."""
        images_dir, output_dir = temp_dirs
        # Don't create any images

        config = AugmentationConfig(output_size=(64, 64))
        pipeline = CardAugmentationPipeline(config)

        generator = SyntheticDatasetGenerator(
            card_repository=mock_repository,
            images_dir=images_dir,
            output_dir=output_dir,
            augmentation_pipeline=pipeline,
        )

        stats = generator.generate(augmentations_per_card=5, seed=42)

        assert stats.total_cards == 1
        assert stats.cards_processed == 0
        assert stats.cards_skipped == 1
        assert "test_card_1" in stats.skipped_cards


class TestGenerateSample:
    """Tests for single-card sample generation."""

    def test_generate_sample_success(
        self,
        mock_repository: MagicMock,
        mock_card: Card,
        sample_image: np.ndarray,
    ) -> None:
        """Sample generation should create images for valid card."""
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            output_dir = Path(tmpdir) / "output"
            images_dir.mkdir()

            # Create test image
            import cv2

            family_dir = images_dir / "test_family"
            family_dir.mkdir()
            image_path = family_dir / "test_card.png"
            cv2.imwrite(str(image_path), sample_image)

            config = AugmentationConfig(output_size=(64, 64))
            pipeline = CardAugmentationPipeline(config)

            generator = SyntheticDatasetGenerator(
                card_repository=mock_repository,
                images_dir=images_dir,
                output_dir=output_dir,
                augmentation_pipeline=pipeline,
            )

            paths = generator.generate_sample("test_card_1", count=3, seed=42)

            assert len(paths) == 3
            for path in paths:
                assert path.exists()

    def test_generate_sample_card_not_found(self, mock_repository: MagicMock) -> None:
        """Sample generation should raise for invalid card ID."""
        mock_repository.get.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = SyntheticDatasetGenerator(
                card_repository=mock_repository,
                images_dir=Path(tmpdir),
                output_dir=Path(tmpdir),
            )

            with pytest.raises(ValueError, match="Card not found"):
                generator.generate_sample("nonexistent_card")


class TestCreateGenerator:
    """Tests for create_generator factory function."""

    def test_create_generator_default(self) -> None:
        """Factory should create generator with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = create_generator(
                images_dir=Path(tmpdir),
                output_dir=Path(tmpdir) / "output",
            )

            assert generator.images_dir == Path(tmpdir)
            assert generator.augmentation_pipeline is not None

    def test_create_generator_custom_config(self) -> None:
        """Factory should accept custom config."""
        config = AugmentationConfig(rotation_limit=15)

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = create_generator(
                images_dir=Path(tmpdir),
                output_dir=Path(tmpdir) / "output",
                config=config,
            )

            assert generator.augmentation_pipeline.config.rotation_limit == 15


class TestPathTraversalSecurity:
    """Security tests for path traversal protection."""

    def test_find_image_path_rejects_parent_traversal(self) -> None:
        """Should reject paths attempting parent directory traversal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()

            # Create a file outside images_dir
            outside_file = Path(tmpdir) / "secret.png"
            outside_file.touch()

            generator = SyntheticDatasetGenerator(images_dir=images_dir)

            # Attempt to access file via parent traversal
            result = generator._find_image_path("../secret.png")

            assert result is None

    def test_find_image_path_rejects_absolute_path(self) -> None:
        """Should reject absolute paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()

            # Create a file somewhere else
            other_file = Path(tmpdir) / "other.png"
            other_file.touch()

            generator = SyntheticDatasetGenerator(images_dir=images_dir)

            # Attempt with absolute path - should return None or be sanitized
            # Note: on Windows, absolute paths in relative_path are handled by Path
            result = generator._find_image_path(str(other_file))

            # The path should either be None or stay within images_dir
            if result is not None:
                assert result.is_relative_to(images_dir.resolve())

    def test_find_image_path_allows_nested_directories(self) -> None:
        """Should allow legitimate nested directory access."""
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir)

            # Create nested structure
            nested = images_dir / "family" / "level1" / "cards"
            nested.mkdir(parents=True)
            image_file = nested / "card.png"
            image_file.touch()

            generator = SyntheticDatasetGenerator(images_dir=images_dir)

            result = generator._find_image_path("family/level1/cards/card.png")

            assert result is not None
            assert result.exists()


class TestImageDimensionValidation:
    """Tests for image dimension validation in _load_image."""

    def test_load_image_handles_grayscale(self) -> None:
        """Should convert grayscale images to RGB."""
        import cv2

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create grayscale image
            gray_image = np.full((100, 80), 128, dtype=np.uint8)
            image_path = Path(tmpdir) / "gray.png"
            cv2.imwrite(str(image_path), gray_image)

            generator = SyntheticDatasetGenerator(images_dir=Path(tmpdir))
            result = generator._load_image(image_path)

            assert result is not None
            # Should be converted to RGB (3 channels)
            assert len(result.shape) == 3
            assert result.shape[2] == 3

    def test_load_image_handles_rgba(self) -> None:
        """Should properly handle RGBA images."""
        import cv2

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create RGBA image
            rgba_image = np.zeros((100, 80, 4), dtype=np.uint8)
            rgba_image[:, :, 0] = 255  # Red
            rgba_image[:, :, 3] = 128  # Semi-transparent
            image_path = Path(tmpdir) / "rgba.png"
            cv2.imwrite(str(image_path), rgba_image)

            generator = SyntheticDatasetGenerator(images_dir=Path(tmpdir))
            result = generator._load_image(image_path)

            assert result is not None
            assert result.shape[2] == 4  # RGBA

    def test_load_image_rejects_too_small(self) -> None:
        """Should reject images smaller than MIN_IMAGE_SIZE."""
        import cv2

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create tiny image (below MIN_IMAGE_SIZE of 16)
            tiny_image = np.zeros((10, 10, 3), dtype=np.uint8)
            image_path = Path(tmpdir) / "tiny.png"
            cv2.imwrite(str(image_path), tiny_image)

            generator = SyntheticDatasetGenerator(images_dir=Path(tmpdir))
            result = generator._load_image(image_path)

            assert result is None

    def test_load_image_accepts_valid_size(self) -> None:
        """Should accept images within valid size range."""
        import cv2

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid sized image
            valid_image = np.zeros((100, 100, 3), dtype=np.uint8)
            image_path = Path(tmpdir) / "valid.png"
            cv2.imwrite(str(image_path), valid_image)

            generator = SyntheticDatasetGenerator(images_dir=Path(tmpdir))
            result = generator._load_image(image_path)

            assert result is not None
            assert result.shape[:2] == (100, 100)
