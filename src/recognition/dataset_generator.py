"""Synthetic dataset generator for card recognition training.

This module generates YOLO-format training datasets by applying augmentations
to card images. The output is compatible with YOLOv5/v8 training pipelines.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
import yaml

from ..cards import CardRepository, get_repository
from .augmentation import AugmentationConfig, CardAugmentationPipeline

logger = logging.getLogger(__name__)


@dataclass
class DatasetStats:
    """Statistics from dataset generation.

    Attributes:
        total_cards: Total number of cards in repository.
        cards_processed: Number of cards with valid images.
        cards_skipped: Number of cards skipped (missing images).
        images_generated: Total augmented images generated.
        train_images: Number of training images.
        val_images: Number of validation images.
        skipped_cards: List of card IDs that were skipped.
    """

    total_cards: int = 0
    cards_processed: int = 0
    cards_skipped: int = 0
    images_generated: int = 0
    train_images: int = 0
    val_images: int = 0
    skipped_cards: list[str] = field(default_factory=list)


class SyntheticDatasetGenerator:
    """Generator for YOLO-format training datasets from card images.

    This class loads card images, applies augmentations, and outputs
    a training dataset in YOLO format with proper train/val splits.

    Example:
        >>> repo = get_repository()
        >>> pipeline = CardAugmentationPipeline()
        >>> generator = SyntheticDatasetGenerator(
        ...     card_repository=repo,
        ...     images_dir=Path("./assets/images"),
        ...     output_dir=Path("./data/training"),
        ...     augmentation_pipeline=pipeline,
        ... )
        >>> stats = generator.generate(augmentations_per_card=100)
        >>> print(f"Generated {stats.images_generated} images")
    """

    # Supported image extensions
    SUPPORTED_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})

    def __init__(
        self,
        card_repository: CardRepository | None = None,
        images_dir: Path | None = None,
        output_dir: Path | None = None,
        augmentation_pipeline: CardAugmentationPipeline | None = None,
    ) -> None:
        """Initialize the dataset generator.

        Args:
            card_repository: Repository for loading card metadata.
                Uses default repository if None.
            images_dir: Directory containing original card images.
                Required for generation.
            output_dir: Directory for generated dataset.
                Required for generation.
            augmentation_pipeline: Pipeline for image augmentation.
                Uses default pipeline if None.
        """
        self.card_repository = card_repository or get_repository()
        self.images_dir = images_dir
        self.output_dir = output_dir
        self.augmentation_pipeline = augmentation_pipeline or CardAugmentationPipeline()

        # Class mapping will be built during generation
        self._class_map: dict[str, int] = {}

    def _build_class_map(self) -> dict[str, int]:
        """Build mapping from card ID to class index.

        Returns:
            Dictionary mapping card_id to class index.
        """
        cards = self.card_repository.get_all()
        # Sort for deterministic ordering
        sorted_ids = sorted(card.id for card in cards)
        return {card_id: idx for idx, card_id in enumerate(sorted_ids)}

    def _find_image_path(self, relative_path: str) -> Path | None:
        """Find the actual image file for a card.

        Handles various image formats and path variations.
        Validates that resolved paths stay within images_dir to prevent
        path traversal attacks.

        Args:
            relative_path: Relative path from card data (e.g., "Lapin lvl 1/Card.png")

        Returns:
            Absolute path to image file, or None if not found or
            path traversal detected.
        """
        if self.images_dir is None:
            return None

        # Resolve images_dir to absolute path for comparison
        images_dir_resolved = self.images_dir.resolve()

        def is_safe_path(path: Path) -> bool:
            """Check that path is within images_dir (no traversal)."""
            try:
                resolved = path.resolve()
                # Check that the resolved path starts with the images directory
                return resolved.is_relative_to(images_dir_resolved)
            except (ValueError, OSError):
                return False

        # Try the exact path first
        exact_path = self.images_dir / relative_path
        if exact_path.exists() and is_safe_path(exact_path):
            return exact_path.resolve()

        # Try with different extensions
        base_path = exact_path.with_suffix("")
        for ext in self.SUPPORTED_EXTENSIONS:
            variant = base_path.with_suffix(ext)
            if variant.exists() and is_safe_path(variant):
                return variant.resolve()

        # Try lowercase path
        parts = Path(relative_path).parts
        lower_path = self.images_dir / Path(*[p.lower() for p in parts])
        if lower_path.exists() and is_safe_path(lower_path):
            return lower_path.resolve()

        return None

    # Image dimension constraints
    MIN_IMAGE_SIZE = 16
    MAX_IMAGE_SIZE = 8192

    def _load_image(self, image_path: Path) -> np.ndarray | None:
        """Load an image file.

        Args:
            image_path: Path to image file.

        Returns:
            Image as numpy array (RGBA or RGB), or None if loading fails.
        """
        try:
            # Read with alpha channel if present
            image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)

            if image is None:
                logger.warning(f"Failed to load image: {image_path}")
                return None

            # Validate dimensions
            if len(image.shape) < 2:
                logger.warning(f"Invalid image shape: {image_path}")
                return None

            height, width = image.shape[:2]
            if (
                height < self.MIN_IMAGE_SIZE
                or width < self.MIN_IMAGE_SIZE
                or height > self.MAX_IMAGE_SIZE
                or width > self.MAX_IMAGE_SIZE
            ):
                logger.warning(
                    f"Image dimensions out of range ({width}x{height}): {image_path}"
                )
                return None

            # Handle different channel configurations
            if len(image.shape) == 2:
                # Grayscale image - convert to RGB
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif image.shape[2] == 4:
                # BGRA - convert to RGBA
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
            elif image.shape[2] == 3:
                # BGR - convert to RGB
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            elif image.shape[2] == 1:
                # Single channel - convert to RGB
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                logger.warning(
                    f"Unsupported channel count ({image.shape[2]}): {image_path}"
                )
                return None

            return image

        except cv2.error as e:
            logger.warning(f"OpenCV error loading image {image_path}: {e}")
            return None
        except OSError as e:
            logger.warning(f"OS error loading image {image_path}: {e}")
            return None

    def _save_image(
        self,
        image: np.ndarray,
        output_path: Path,
    ) -> bool:
        """Save an image to disk.

        Args:
            image: Image as numpy array (RGB).
            output_path: Path to save image.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Convert RGB to BGR for OpenCV
            bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(output_path), bgr_image)
            return True
        except cv2.error as e:
            logger.warning(f"OpenCV error saving image {output_path}: {e}")
            return False
        except OSError as e:
            logger.warning(f"OS error saving image {output_path}: {e}")
            return False

    def _save_label(
        self,
        bbox: tuple[float, float, float, float],
        class_id: int,
        output_path: Path,
    ) -> bool:
        """Save YOLO label file.

        Args:
            bbox: Bounding box as (x_center, y_center, width, height).
            class_id: Class index for this card.
            output_path: Path to save label file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            x_center, y_center, width, height = bbox

            # Skip if bbox is invalid (empty mask)
            if width <= 0 or height <= 0:
                return False

            with open(output_path, "w") as f:
                f.write(
                    f"{class_id} {x_center:.6f} {y_center:.6f} "
                    f"{width:.6f} {height:.6f}\n"
                )
            return True
        except OSError as e:
            logger.warning(f"OS error saving label {output_path}: {e}")
            return False
        except ValueError as e:
            logger.warning(f"Value error saving label {output_path}: {e}")
            return False

    def _create_output_structure(self) -> None:
        """Create the output directory structure."""
        if self.output_dir is None:
            raise ValueError("output_dir must be set before generation")

        dirs = [
            self.output_dir / "images" / "train",
            self.output_dir / "images" / "val",
            self.output_dir / "labels" / "train",
            self.output_dir / "labels" / "val",
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _write_data_yaml(self) -> None:
        """Write the data.yaml file for YOLO training."""
        if self.output_dir is None:
            return

        # Build names list in class order
        names = {idx: card_id for card_id, idx in self._class_map.items()}
        names_list = [names[i] for i in range(len(names))]

        data = {
            "path": str(self.output_dir.absolute()),
            "train": "images/train",
            "val": "images/val",
            "nc": len(self._class_map),
            "names": names_list,
        }

        yaml_path = self.output_dir / "data.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Wrote data.yaml with {len(names_list)} classes")

    def generate(
        self,
        augmentations_per_card: int = 100,
        val_split: float = 0.2,
        seed: int = 42,
    ) -> DatasetStats:
        """Generate the full training dataset.

        Args:
            augmentations_per_card: Number of augmented images per card.
            val_split: Fraction of images for validation set.
            seed: Random seed for reproducibility.

        Returns:
            DatasetStats with generation statistics.

        Raises:
            ValueError: If images_dir or output_dir is not set.
        """
        if self.images_dir is None:
            raise ValueError("images_dir must be set before generation")
        if self.output_dir is None:
            raise ValueError("output_dir must be set before generation")

        # Set random seed
        np.random.seed(seed)

        # Initialize stats
        stats = DatasetStats()

        # Load all cards
        cards = self.card_repository.get_all()
        stats.total_cards = len(cards)

        # Build class mapping
        self._class_map = self._build_class_map()

        # Create output structure
        self._create_output_structure()

        logger.info(f"Starting generation for {stats.total_cards} cards")
        logger.info(f"Augmentations per card: {augmentations_per_card}")
        logger.info(f"Val split: {val_split}")

        # Process each card
        for card in cards:
            # Find image
            image_path = self._find_image_path(card.image_path)

            if image_path is None:
                logger.warning(f"Missing image for card: {card.id} ({card.image_path})")
                stats.cards_skipped += 1
                stats.skipped_cards.append(card.id)
                continue

            # Load image
            image = self._load_image(image_path)

            if image is None:
                stats.cards_skipped += 1
                stats.skipped_cards.append(card.id)
                continue

            # Get class ID
            class_id = self._class_map[card.id]

            # Determine train/val split for this card's augmentations
            val_count = int(augmentations_per_card * val_split)
            train_count = augmentations_per_card - val_count

            # Generate augmentations
            card_seed = seed + class_id * 10000  # Unique seed per card

            # Generate training images
            for i in range(train_count):
                np.random.seed(card_seed + i)
                augmented, bbox = self.augmentation_pipeline.augment(
                    image, return_bbox=True
                )

                filename = f"{card.id}_{i:04d}"
                img_path = self.output_dir / "images" / "train" / f"{filename}.jpg"
                lbl_path = self.output_dir / "labels" / "train" / f"{filename}.txt"

                if self._save_image(augmented, img_path):
                    if self._save_label(bbox, class_id, lbl_path):
                        stats.train_images += 1
                        stats.images_generated += 1

            # Generate validation images
            for i in range(val_count):
                np.random.seed(card_seed + train_count + i)
                augmented, bbox = self.augmentation_pipeline.augment(
                    image, return_bbox=True
                )

                filename = f"{card.id}_{train_count + i:04d}"
                img_path = self.output_dir / "images" / "val" / f"{filename}.jpg"
                lbl_path = self.output_dir / "labels" / "val" / f"{filename}.txt"

                if self._save_image(augmented, img_path):
                    if self._save_label(bbox, class_id, lbl_path):
                        stats.val_images += 1
                        stats.images_generated += 1

            stats.cards_processed += 1

            if stats.cards_processed % 10 == 0:
                logger.info(
                    f"Processed {stats.cards_processed}/{stats.total_cards} cards"
                )

        # Write data.yaml
        self._write_data_yaml()

        logger.info("Generation complete:")
        logger.info(f"  Cards processed: {stats.cards_processed}")
        logger.info(f"  Cards skipped: {stats.cards_skipped}")
        logger.info(f"  Total images: {stats.images_generated}")
        logger.info(f"  Train images: {stats.train_images}")
        logger.info(f"  Val images: {stats.val_images}")

        return stats

    def generate_sample(
        self,
        card_id: str,
        count: int = 10,
        output_dir: Path | None = None,
        seed: int = 42,
    ) -> list[Path]:
        """Generate sample augmentations for a single card.

        Useful for testing and visualization.

        Args:
            card_id: ID of the card to augment.
            count: Number of samples to generate.
            output_dir: Directory for output. Uses self.output_dir if None.
            seed: Random seed for reproducibility.

        Returns:
            List of paths to generated images.

        Raises:
            ValueError: If card not found or image missing.
        """
        output_dir = output_dir or self.output_dir
        if output_dir is None:
            raise ValueError("output_dir must be specified")

        # Get card
        card = self.card_repository.get(card_id)
        if card is None:
            raise ValueError(f"Card not found: {card_id}")

        # Find image
        if self.images_dir is None:
            raise ValueError("images_dir must be set")

        image_path = self._find_image_path(card.image_path)
        if image_path is None:
            raise ValueError(f"Image not found for card: {card_id}")

        # Load image
        image = self._load_image(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Create output directory
        sample_dir = output_dir / "samples" / card_id
        sample_dir.mkdir(parents=True, exist_ok=True)

        # Generate samples
        np.random.seed(seed)
        generated_paths = []

        for i in range(count):
            augmented, bbox = self.augmentation_pipeline.augment(
                image, return_bbox=True
            )

            output_path = sample_dir / f"sample_{i:03d}.jpg"
            if self._save_image(augmented, output_path):
                generated_paths.append(output_path)

        logger.info(f"Generated {len(generated_paths)} samples for {card_id}")
        return generated_paths


def create_generator(
    images_dir: Path,
    output_dir: Path,
    config: AugmentationConfig | None = None,
) -> SyntheticDatasetGenerator:
    """Create a dataset generator with standard configuration.

    Args:
        images_dir: Directory containing card images.
        output_dir: Directory for generated dataset.
        config: Optional augmentation configuration.

    Returns:
        Configured SyntheticDatasetGenerator instance.
    """
    pipeline = CardAugmentationPipeline(config)
    return SyntheticDatasetGenerator(
        images_dir=images_dir,
        output_dir=output_dir,
        augmentation_pipeline=pipeline,
    )
