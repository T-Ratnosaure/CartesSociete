#!/usr/bin/env python
"""Validate card data against source images.

This script helps verify that card JSON data matches the actual card images
by generating a validation report and optionally displaying cards side-by-side
with their images for manual verification.

Usage:
    # Run from project root:
    uv run python -m scripts.validate_cards --image-dir /path/to/images

    # Or with the script directly (after installing in editable mode):
    python scripts/validate_cards.py --image-dir /path/to/images

Environment Variables:
    CARTES_SOCIETE_IMAGES: Default path for card images (optional)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.cards import CardRepository

# Import cards module - works when run as module or when package is installed
try:
    from src.cards import CardRepository
except ImportError:
    from cards import CardRepository  # type: ignore[import-not-found,no-redef]


def validate_image_paths(repo: CardRepository, image_dir: Path) -> list[dict]:
    """Validate that all card image paths exist.

    Args:
        repo: The card repository to validate.
        image_dir: Directory containing card images.

    Returns:
        List of validation issues found.
    """
    issues = []
    cards = repo.get_all()

    for card in cards:
        image_path = image_dir / card.image_path
        if not image_path.exists():
            issues.append(
                {
                    "type": "missing_image",
                    "card_id": card.id,
                    "card_name": card.name,
                    "expected_path": str(image_path),
                }
            )

    return issues


def find_unregistered_images(repo: CardRepository, image_dir: Path) -> list[Path]:
    """Find images that don't have corresponding card data.

    Args:
        repo: The card repository.
        image_dir: Directory containing card images.

    Returns:
        List of image paths without card data.
    """
    # Get all registered image paths
    registered_images = {card.image_path for card in repo.get_all()}

    # Find all images
    all_images = list(image_dir.rglob("*.png"))

    # Filter to unregistered
    unregistered = []
    for img_path in all_images:
        relative_path = img_path.relative_to(image_dir)
        if str(relative_path) not in registered_images:
            unregistered.append(img_path)

    return unregistered


def generate_card_template(
    image_path: Path, family_from_dir: str | None = None
) -> dict:
    """Generate a template JSON for a card based on image path.

    Args:
        image_path: Path to the card image.
        family_from_dir: Family inferred from directory name.

    Returns:
        Dictionary template for card JSON.
    """
    name = image_path.stem.strip()

    # Try to infer family from directory
    family = family_from_dir or "Unknown"
    level = None

    parent_dir = image_path.parent.name.lower()
    if "lvl 1" in parent_dir or "lvl1" in parent_dir:
        level = 1
    elif "lvl 2" in parent_dir or "lvl2" in parent_dir:
        level = 2

    # Infer family from directory
    family_map = {
        "cyborg": "Cyborg",
        "nature": "Nature",
        "atlantide": "Atlantide",
        "ninja": "Ninja",
        "neige": "Neige",
        "lapin": "Lapin",
        "raton": "Raton",
        "hall of win": "Hall of win",
    }

    for key, value in family_map.items():
        if key in parent_dir:
            family = value
            break

    # Generate card ID
    card_id = f"{family.lower().replace(' ', '_')}_{name.lower().replace(' ', '_')}"
    if level:
        card_id += f"_{level}"

    card_type = "creature"
    if family == "Arme" or "arme" in name.lower():
        card_type = "weapon"
        level = None
    elif (
        "demon" in name.lower()
        or "diablotin" in name.lower()
        or "succube" in name.lower()
    ):
        card_type = "demon"
        family = "Demon"
        level = None

    return {
        "id": card_id,
        "name": name,
        "card_type": card_type,
        "level": level,
        "movement": 1,
        "family": family,
        "card_class": "TODO",
        "family_abilities": {"scaling": []},
        "class_abilities": {"scaling": []},
        "bonus_text": None,
        "health": 0,
        "attack": 0,
        "image_path": str(image_path.name)
        if image_path.parent.name == image_path.parent.parent.name
        else f"{image_path.parent.name}/{image_path.name}",
    }


def generate_validation_report(
    repo: CardRepository,
    image_dir: Path,
    output_file: Path | None = None,
) -> str:
    """Generate a comprehensive validation report.

    Args:
        repo: The card repository to validate.
        image_dir: Directory containing card images.
        output_file: Optional file to write the report to.

    Returns:
        The validation report as a string.
    """
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("CARTESSOCIETE CARD VALIDATION REPORT")
    report_lines.append("=" * 60)
    report_lines.append("")

    # Count cards
    cards = repo.get_all()
    report_lines.append(f"Total cards in database: {len(cards)}")
    report_lines.append("")

    # Validate image paths
    report_lines.append("-" * 40)
    report_lines.append("IMAGE PATH VALIDATION")
    report_lines.append("-" * 40)

    issues = validate_image_paths(repo, image_dir)
    if issues:
        report_lines.append(f"Found {len(issues)} missing images:")
        for issue in issues:
            report_lines.append(f"  - {issue['card_name']} ({issue['card_id']})")
            report_lines.append(f"    Expected: {issue['expected_path']}")
    else:
        report_lines.append("All card images found!")

    report_lines.append("")

    # Find unregistered images
    report_lines.append("-" * 40)
    report_lines.append("UNREGISTERED IMAGES")
    report_lines.append("-" * 40)

    unregistered = find_unregistered_images(repo, image_dir)
    if unregistered:
        report_lines.append(f"Found {len(unregistered)} images without card data:")
        for img in sorted(unregistered):
            report_lines.append(f"  - {img.relative_to(image_dir)}")
    else:
        report_lines.append("All images have corresponding card data!")

    report_lines.append("")

    # Summary by family
    report_lines.append("-" * 40)
    report_lines.append("CARDS BY FAMILY")
    report_lines.append("-" * 40)

    from collections import Counter

    family_counts = Counter(card.family.value for card in cards)
    for family, count in sorted(family_counts.items()):
        report_lines.append(f"  {family}: {count}")

    report_lines.append("")

    # Summary by class
    report_lines.append("-" * 40)
    report_lines.append("CARDS BY CLASS")
    report_lines.append("-" * 40)

    class_counts = Counter(card.card_class.value for card in cards)
    for card_class, count in sorted(class_counts.items()):
        report_lines.append(f"  {card_class}: {count}")

    report_lines.append("")
    report_lines.append("=" * 60)

    report = "\n".join(report_lines)

    if output_file:
        output_file.write_text(report, encoding="utf-8")

    return report


def generate_templates_for_missing(image_dir: Path, output_file: Path) -> None:
    """Generate JSON templates for all unregistered images.

    Args:
        image_dir: Directory containing card images.
        output_file: File to write templates to.
    """
    repo = CardRepository(Path(__file__).parent.parent / "data" / "cards")
    try:
        repo.load()
    except FileNotFoundError:
        print("Warning: No card data found, generating templates for all images")

    unregistered = find_unregistered_images(repo, image_dir)

    templates = []
    for img_path in sorted(unregistered):
        template = generate_card_template(img_path)
        template["image_path"] = str(img_path.relative_to(image_dir))
        templates.append(template)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(templates)} card templates in {output_file}")


def main() -> int:
    """Main entry point for validation script.

    Returns:
        Exit code (0 for success, 1 for validation errors).
    """
    # Get default image directory from environment variable
    default_image_dir = os.environ.get("CARTES_SOCIETE_IMAGES")
    if default_image_dir:
        default_image_dir = Path(default_image_dir)

    parser = argparse.ArgumentParser(
        description="Validate card data against source images"
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=default_image_dir,
        required=default_image_dir is None,
        help="Directory containing card images (or set CARTES_SOCIETE_IMAGES env var)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "cards",
        help="Directory containing card JSON files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file to write validation report",
    )
    parser.add_argument(
        "--generate-templates",
        type=Path,
        help="Generate JSON templates for missing cards to this file",
    )
    parser.add_argument(
        "--generate-gallery",
        type=Path,
        help="Generate HTML gallery of all registered cards",
    )

    args = parser.parse_args()

    # Initialize repository
    repo = CardRepository(args.data_dir)
    try:
        repo.load()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    # Generate templates if requested
    if args.generate_templates:
        generate_templates_for_missing(args.image_dir, args.generate_templates)
        return 0

    # Generate gallery if requested
    if args.generate_gallery:
        # Lazy import to avoid loading renderer when not needed
        try:
            from src.cards import CardRenderer
        except ImportError:
            from cards import CardRenderer  # type: ignore[import-not-found,no-redef]

        renderer = CardRenderer(image_base_path=args.image_dir)
        cards = repo.get_all()
        renderer.save_gallery(cards, args.generate_gallery)
        print(f"Generated gallery with {len(cards)} cards: {args.generate_gallery}")
        return 0

    # Generate and print validation report
    report = generate_validation_report(repo, args.image_dir, args.output)
    print(report)

    # Return error code if there are issues
    issues = validate_image_paths(repo, args.image_dir)
    unregistered = find_unregistered_images(repo, args.image_dir)

    if issues:
        print(f"\nERROR: {len(issues)} cards have missing images")
        return 1

    if unregistered:
        print(f"\nWARNING: {len(unregistered)} images are not registered")
        # Not an error, just a warning

    return 0


if __name__ == "__main__":
    sys.exit(main())
