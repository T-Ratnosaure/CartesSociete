"""Image augmentation pipeline for card recognition training data.

This module provides a configurable augmentation pipeline that transforms
card images to simulate real-world camera conditions, improving model
robustness when deployed on mobile devices.
"""

from dataclasses import dataclass, field

import albumentations as alb
import cv2
import numpy as np


@dataclass
class AugmentationConfig:
    """Configuration for card image augmentation.

    Attributes:
        rotation_limit: Maximum rotation angle in degrees (-limit to +limit).
        scale_range: Min and max scale factors for resizing.
        shift_limit: Maximum shift as fraction of image size.
        perspective_scale: Strength of perspective transform (0-1).
        brightness_limit: Maximum brightness adjustment as fraction.
        contrast_limit: Maximum contrast adjustment as fraction.
        saturation_range: Min and max saturation multipliers.
        hue_shift_limit: Maximum hue shift in degrees.
        blur_limit: Maximum Gaussian blur kernel size (odd number).
        noise_var_limit: Maximum Gaussian noise variance.
        output_size: Target output image size (width, height).
        jpeg_quality_range: Range of JPEG quality for compression artifacts.
    """

    # Geometric transforms
    rotation_limit: int = 30
    scale_range: tuple[float, float] = (0.7, 1.3)
    shift_limit: float = 0.1
    perspective_scale: float = 0.1

    # Photometric transforms
    brightness_limit: float = 0.2
    contrast_limit: float = 0.2
    saturation_range: tuple[float, float] = (0.8, 1.2)
    hue_shift_limit: int = 10
    blur_limit: int = 3
    noise_std_range: tuple[float, float] = (0.0, 0.06)  # Normalized [0,1], ~15/255

    # Output settings
    output_size: tuple[int, int] = (640, 640)
    jpeg_quality_range: tuple[int, int] = (70, 95)

    # Background settings
    background_colors: list[tuple[int, int, int]] = field(
        default_factory=lambda: [
            (34, 139, 34),  # Forest green (felt)
            (139, 69, 19),  # Saddle brown (wood)
            (47, 79, 79),  # Dark slate gray
            (105, 105, 105),  # Dim gray
            (255, 248, 220),  # Cornsilk (light table)
            (0, 0, 0),  # Black
            (255, 255, 255),  # White
        ]
    )


class CardAugmentationPipeline:
    """Pipeline for augmenting card images for training data generation.

    This class creates realistic variations of card images by applying
    geometric and photometric transforms that simulate real-world
    camera conditions.

    Example:
        >>> config = AugmentationConfig(rotation_limit=45)
        >>> pipeline = CardAugmentationPipeline(config)
        >>> augmented = pipeline.augment(card_image)
    """

    def __init__(self, config: AugmentationConfig | None = None) -> None:
        """Initialize the augmentation pipeline.

        Args:
            config: Augmentation configuration. Uses defaults if None.
        """
        self.config = config or AugmentationConfig()
        self._transform = self._build_transform()
        self._background_transform = self._build_background_transform()

    def _build_transform(self) -> alb.Compose:
        """Build the Albumentations transform pipeline.

        Returns:
            Composed transform pipeline.
        """
        cfg = self.config

        return alb.Compose(
            [
                # Geometric transforms
                alb.Affine(
                    rotate=(-cfg.rotation_limit, cfg.rotation_limit),
                    scale=(cfg.scale_range[0], cfg.scale_range[1]),
                    translate_percent={
                        "x": (-cfg.shift_limit, cfg.shift_limit),
                        "y": (-cfg.shift_limit, cfg.shift_limit),
                    },
                    border_mode=cv2.BORDER_CONSTANT,
                    fill=0,  # Transparent for RGBA
                    p=1.0,
                ),
                alb.Perspective(
                    scale=(0.02, cfg.perspective_scale),
                    keep_size=True,
                    fill=0,
                    p=0.5,
                ),
                # Photometric transforms
                alb.RandomBrightnessContrast(
                    brightness_limit=cfg.brightness_limit,
                    contrast_limit=cfg.contrast_limit,
                    p=0.8,
                ),
                alb.HueSaturationValue(
                    hue_shift_limit=cfg.hue_shift_limit,
                    sat_shift_limit=int(
                        (cfg.saturation_range[1] - cfg.saturation_range[0]) * 50
                    ),
                    val_shift_limit=0,
                    p=0.5,
                ),
            ],
            additional_targets={"mask": "mask"},
        )

    def _build_background_transform(self) -> alb.Compose:
        """Build transforms applied after background composition.

        Returns:
            Composed post-composition transform pipeline.
        """
        cfg = self.config

        return alb.Compose(
            [
                # Blur (simulates focus issues)
                alb.GaussianBlur(
                    blur_limit=(1, cfg.blur_limit),
                    p=0.3,
                ),
                # Noise (simulates sensor noise)
                alb.GaussNoise(
                    std_range=cfg.noise_std_range,
                    p=0.4,
                ),
                # JPEG compression artifacts
                alb.ImageCompression(
                    quality_range=cfg.jpeg_quality_range,
                    p=0.3,
                ),
            ]
        )

    def augment(
        self,
        image: np.ndarray,
        return_bbox: bool = False,
    ) -> np.ndarray | tuple[np.ndarray, tuple[float, float, float, float]]:
        """Apply augmentation to a card image.

        The image should have an alpha channel (RGBA) for proper background
        composition. If RGB, a full-opacity alpha channel is added.
        Grayscale images are converted to RGB first.

        Args:
            image: Input card image as numpy array.
                Supports (H, W), (H, W, 1), (H, W, 3), or (H, W, 4).
            return_bbox: If True, also return the bounding box of the card.

        Returns:
            Augmented image as numpy array (H, W, 3).
            If return_bbox is True, returns tuple of (image, bbox) where
            bbox is (x_center, y_center, width, height) normalized to [0, 1].
        """
        # Handle grayscale images
        if len(image.shape) == 2:
            # Grayscale (H, W) -> RGB (H, W, 3)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif len(image.shape) == 3 and image.shape[2] == 1:
            # Single channel (H, W, 1) -> RGB (H, W, 3)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        # Ensure RGBA format
        if len(image.shape) == 3 and image.shape[2] == 3:
            alpha = np.full((image.shape[0], image.shape[1], 1), 255, dtype=np.uint8)
            image = np.concatenate([image, alpha], axis=2)

        # Create mask from alpha channel
        mask = image[:, :, 3]

        # Apply geometric and photometric transforms
        transformed = self._transform(image=image[:, :, :3], mask=mask)
        transformed_image = transformed["image"]
        transformed_mask = transformed["mask"]

        # Composite onto background
        composited = self._composite_on_background(transformed_image, transformed_mask)

        # Resize to output size
        composited = cv2.resize(
            composited,
            self.config.output_size,
            interpolation=cv2.INTER_LINEAR,
        )

        # Resize mask for bbox calculation
        resized_mask = cv2.resize(
            transformed_mask,
            self.config.output_size,
            interpolation=cv2.INTER_NEAREST,
        )

        # Apply post-composition transforms
        final = self._background_transform(image=composited)["image"]

        if return_bbox:
            bbox = self._calculate_bbox(resized_mask)
            return final, bbox

        return final

    def _composite_on_background(
        self,
        image: np.ndarray,
        mask: np.ndarray,
    ) -> np.ndarray:
        """Composite card image onto a random background.

        Args:
            image: Card image (H, W, 3).
            mask: Alpha mask (H, W).

        Returns:
            Composited image (H, W, 3).
        """
        # Select random background color
        bg_color = self.config.background_colors[
            np.random.randint(len(self.config.background_colors))
        ]

        # Create background
        background = np.full_like(image, bg_color, dtype=np.uint8)

        # Normalize mask to [0, 1]
        alpha = mask.astype(np.float32) / 255.0
        alpha = alpha[:, :, np.newaxis]

        # Composite: foreground * alpha + background * (1 - alpha)
        composited = (image * alpha + background * (1 - alpha)).astype(np.uint8)

        return composited

    def _calculate_bbox(
        self,
        mask: np.ndarray,
    ) -> tuple[float, float, float, float]:
        """Calculate bounding box from mask in YOLO format.

        Args:
            mask: Binary mask of card location (H, W).

        Returns:
            Bounding box as (x_center, y_center, width, height),
            all normalized to [0, 1]. Returns (0.5, 0.5, 0, 0) if
            mask is empty.
        """
        # Find non-zero pixels
        coords = np.where(mask > 127)

        if len(coords[0]) == 0:
            # Empty mask - return centered zero-size box
            return (0.5, 0.5, 0.0, 0.0)

        y_min, y_max = coords[0].min(), coords[0].max()
        x_min, x_max = coords[1].min(), coords[1].max()

        h, w = mask.shape

        # Calculate normalized center and size
        x_center = ((x_min + x_max) / 2) / w
        y_center = ((y_min + y_max) / 2) / h
        width = (x_max - x_min) / w
        height = (y_max - y_min) / h

        return (x_center, y_center, width, height)

    def augment_batch(
        self,
        image: np.ndarray,
        count: int,
        seed: int | None = None,
    ) -> list[tuple[np.ndarray, tuple[float, float, float, float]]]:
        """Generate multiple augmented versions of an image.

        Args:
            image: Input card image.
            count: Number of augmented images to generate.
            seed: Random seed for reproducibility. If None, uses random state.

        Returns:
            List of (augmented_image, bbox) tuples.
        """
        if seed is not None:
            np.random.seed(seed)

        results = []
        for i in range(count):
            # Set per-image seed for reproducibility
            if seed is not None:
                np.random.seed(seed + i)

            augmented, bbox = self.augment(image, return_bbox=True)
            results.append((augmented, bbox))

        return results


def create_default_pipeline() -> CardAugmentationPipeline:
    """Create augmentation pipeline with default settings.

    Returns:
        Configured CardAugmentationPipeline instance.
    """
    return CardAugmentationPipeline(AugmentationConfig())


def create_conservative_pipeline() -> CardAugmentationPipeline:
    """Create augmentation pipeline with conservative settings.

    Uses smaller transform ranges for cleaner training data.

    Returns:
        Configured CardAugmentationPipeline instance.
    """
    config = AugmentationConfig(
        rotation_limit=15,
        scale_range=(0.85, 1.15),
        shift_limit=0.05,
        perspective_scale=0.05,
        brightness_limit=0.1,
        contrast_limit=0.1,
        blur_limit=1,
        noise_std_range=(0.0, 0.02),  # ~5/255
    )
    return CardAugmentationPipeline(config)


def create_aggressive_pipeline() -> CardAugmentationPipeline:
    """Create augmentation pipeline with aggressive settings.

    Uses larger transform ranges for maximum variety.

    Returns:
        Configured CardAugmentationPipeline instance.
    """
    config = AugmentationConfig(
        rotation_limit=45,
        scale_range=(0.5, 1.5),
        shift_limit=0.15,
        perspective_scale=0.15,
        brightness_limit=0.3,
        contrast_limit=0.3,
        blur_limit=5,
        noise_std_range=(0.0, 0.1),  # ~25/255
    )
    return CardAugmentationPipeline(config)
