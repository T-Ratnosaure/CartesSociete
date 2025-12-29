"""Card visual renderer for displaying cards in-game.

This module provides utilities to render cards as visual components,
either as ASCII art for terminal display or as HTML for web-based interfaces.
"""

from html import escape as html_escape
from pathlib import Path

from .models import Card


class PathTraversalError(ValueError):
    """Raised when an image path attempts to escape the base directory."""

    pass


def _validate_image_path(image_path: str, base_path: Path | None) -> str:
    """Validate and resolve an image path, preventing path traversal attacks.

    Args:
        image_path: The image path from card data.
        base_path: Optional base path for images.

    Returns:
        The validated image path or src string.

    Raises:
        PathTraversalError: If the path attempts to escape the base directory.
    """
    if base_path is None:
        # Without a base path, just return the image path as-is
        # The caller is responsible for ensuring safety
        return image_path

    # Resolve the full path
    resolved = (base_path / image_path).resolve()
    base_resolved = base_path.resolve()

    # Check that the resolved path is within the base directory
    try:
        resolved.relative_to(base_resolved)
    except ValueError:
        raise PathTraversalError(
            f"Image path '{image_path}' attempts to escape base directory"
        )

    return str(resolved)


def render_card_ascii(card: Card, width: int = 40) -> str:
    """Render a card as ASCII art for terminal display.

    Args:
        card: The card to render.
        width: The width of the rendered card in characters.

    Returns:
        A multi-line string representing the card.
    """
    border = "+" + "-" * (width - 2) + "+"

    def center_text(text: str, w: int = width - 4) -> str:
        """Center text within a given width."""
        return text.center(w)

    def left_right(left: str, right: str, w: int = width - 4) -> str:
        """Format two strings on left and right sides within width w."""
        total_len = len(left) + len(right)
        if total_len >= w:
            # Truncate if necessary
            return (left + " " + right)[:w]
        space = w - total_len
        return left + " " * space + right

    def make_line(content: str) -> str:
        """Create a line with borders, ensuring exact width."""
        inner = content[: width - 2]
        return "|" + inner.ljust(width - 2) + "|"

    lines = [border]

    # Header: Tier | Name | Cost
    cost_str = str(card.cost) if card.cost else "X"
    header = f" ^{card.level}  {card.name}  ({cost_str})"
    lines.append(make_line(center_text(header)))
    lines.append("|" + "-" * (width - 2) + "|")

    # Family | Class
    family_class = left_right(card.family.value, card.card_class.value, width - 6)
    lines.append(make_line("  " + family_class))
    lines.append("|" + "-" * (width - 2) + "|")

    # Family Abilities
    if card.family_abilities.passive:
        passive = card.family_abilities.passive[: width - 6]
        lines.append(make_line("  " + passive))

    for ability in card.family_abilities.scaling:
        ability_text = f"{ability.threshold}: {ability.effect}"[: width - 6]
        lines.append(make_line("  " + ability_text))

    lines.append(make_line(""))

    # Class Abilities
    if card.class_abilities.passive:
        passive = card.class_abilities.passive[: width - 6]
        lines.append(make_line("  " + passive))

    for ability in card.class_abilities.scaling:
        ability_text = f"{ability.threshold}: {ability.effect}"[: width - 6]
        lines.append(make_line("  " + ability_text))

    for ability in card.class_abilities.conditional:
        ability_text = f"{ability.condition}: {ability.effect}"[: width - 6]
        lines.append(make_line("  " + ability_text))

    lines.append("|" + "-" * (width - 2) + "|")

    # Bonus text
    if card.bonus_text:
        bonus = card.bonus_text[: width - 6]
        lines.append(make_line("  " + bonus))
        lines.append("|" + "-" * (width - 2) + "|")

    # Stats: Health | Attack
    stats = left_right(f"<3 {card.health}", f"X {card.attack}", width - 6)
    lines.append(make_line("  " + stats))
    lines.append(border)

    return "\n".join(lines)


def render_card_html(
    card: Card,
    image_base_path: Path | None = None,
    include_image: bool = True,
) -> str:
    """Render a card as an HTML component.

    Args:
        card: The card to render.
        image_base_path: Base path for card images. If None, uses relative path.
        include_image: Whether to include the card image.

    Returns:
        An HTML string representing the card.

    Raises:
        PathTraversalError: If the image path attempts directory traversal.
    """
    # Escape all user-controllable strings to prevent XSS
    safe_name = html_escape(card.name)
    safe_id = html_escape(card.id)
    safe_family = html_escape(card.family.value)
    safe_class = html_escape(card.card_class.value)

    # Determine card type class for styling
    type_class = html_escape(card.card_type.value)
    cost_class = f"level-{card.cost}" if card.cost else "level-x"

    # Build and validate image path
    image_src = _validate_image_path(card.image_path, image_base_path)
    safe_image_src = html_escape(image_src)

    # Build family abilities HTML (with escaping)
    family_abilities_html = ""
    if card.family_abilities.passive:
        safe_passive = html_escape(card.family_abilities.passive)
        family_abilities_html += f'<div class="ability passive">{safe_passive}</div>'
    for ability in card.family_abilities.scaling:
        safe_effect = html_escape(ability.effect)
        family_abilities_html += (
            f'<div class="ability scaling">'
            f'<span class="threshold">{ability.threshold}:</span> '
            f"{safe_effect}</div>"
        )

    # Build class abilities HTML (with escaping)
    class_abilities_html = ""
    if card.class_abilities.passive:
        safe_passive = html_escape(card.class_abilities.passive)
        class_abilities_html += f'<div class="ability passive">{safe_passive}</div>'
    for ability in card.class_abilities.scaling:
        safe_effect = html_escape(ability.effect)
        class_abilities_html += (
            f'<div class="ability scaling">'
            f'<span class="threshold">{ability.threshold}:</span> '
            f"{safe_effect}</div>"
        )
    for ability in card.class_abilities.conditional:
        safe_condition = html_escape(ability.condition)
        safe_effect = html_escape(ability.effect)
        class_abilities_html += (
            f'<div class="ability conditional">'
            f'<span class="condition">{safe_condition}:</span> '
            f"{safe_effect}</div>"
        )

    # Build bonus HTML (with escaping)
    bonus_html = ""
    if card.bonus_text:
        safe_bonus = html_escape(card.bonus_text)
        bonus_html = f'<div class="bonus-text">{safe_bonus}</div>'

    # Cost display
    cost_display = str(card.cost) if card.cost else "X"

    # Image section
    image_html = ""
    if include_image:
        image_html = (
            f'<div class="card-image">'
            f'<img src="{safe_image_src}" alt="{safe_name}" /></div>'
        )

    html = f"""
<div class="card {type_class} {cost_class}" data-card-id="{safe_id}">
    <div class="card-header">
        <span class="tier">^{card.level}</span>
        <span class="name">{safe_name}</span>
        <span class="cost">{cost_display}</span>
    </div>
    {image_html}
    <div class="card-body">
        <div class="type-row">
            <span class="family">{safe_family}</span>
            <span class="card-class">{safe_class}</span>
        </div>
        <div class="abilities-section">
            <div class="family-abilities">
                {family_abilities_html}
            </div>
            <div class="class-abilities">
                {class_abilities_html}
            </div>
        </div>
        {bonus_html}
    </div>
    <div class="card-footer">
        <span class="health"><span class="icon">&#10084;</span> {card.health}</span>
        <span class="attack"><span class="icon">&#9876;</span> {card.attack}</span>
    </div>
</div>
"""
    return html.strip()


def get_card_css() -> str:
    """Get the CSS styles for card components.

    Returns:
        CSS string for styling cards.
    """
    return """
/* CartesSociete Card Styles */
.card {
    width: 280px;
    border: 3px solid #8B4513;
    border-radius: 12px;
    background: linear-gradient(135deg, #D4A574 0%, #C4956A 50%, #B8865A 100%);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    overflow: hidden;
}

.card.level-1 {
    background: linear-gradient(135deg, #D4A574 0%, #C4956A 50%, #B8865A 100%);
}

.card.level-2 {
    background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 50%, #909090 100%);
    border-color: #696969;
}

.card.weapon, .card.demon {
    background: linear-gradient(135deg, #8B0000 0%, #A52A2A 50%, #CD5C5C 100%);
    border-color: #4B0000;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.2);
    border-bottom: 2px solid #8B4513;
}

.card-header .tier {
    font-size: 14px;
    font-weight: bold;
    background: #F5DEB3;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #8B4513;
}

.card-header .name {
    font-size: 16px;
    font-weight: bold;
    color: #2F1810;
    text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.3);
    flex: 1;
    text-align: center;
    margin: 0 8px;
}

.card-header .cost {
    font-size: 18px;
    font-weight: bold;
    background: #F5DEB3;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #8B4513;
}

.card-image {
    width: 100%;
    height: 160px;
    overflow: hidden;
    border-bottom: 2px solid #8B4513;
}

.card-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.card-body {
    padding: 8px;
}

.type-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 8px;
    background: #F5DEB3;
    border-radius: 6px;
    margin-bottom: 8px;
    border: 1px solid #8B4513;
}

.type-row .family,
.type-row .card-class {
    font-weight: bold;
    font-size: 14px;
    color: #2F1810;
}

.abilities-section {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
}

.family-abilities,
.class-abilities {
    flex: 1;
    background: #F5DEB3;
    border-radius: 6px;
    padding: 6px;
    font-size: 11px;
    border: 1px solid #8B4513;
}

.ability {
    margin-bottom: 4px;
    color: #2F1810;
}

.ability .threshold,
.ability .condition {
    font-weight: bold;
    color: #8B0000;
}

.ability.passive {
    font-style: italic;
    color: #4B0082;
}

.bonus-text {
    background: #FFE4B5;
    border-radius: 6px;
    padding: 6px;
    font-size: 11px;
    text-align: center;
    font-style: italic;
    color: #8B4513;
    border: 1px dashed #8B4513;
    margin-bottom: 8px;
}

.card-footer {
    display: flex;
    justify-content: space-between;
    padding: 8px 16px;
    background: rgba(0, 0, 0, 0.2);
    border-top: 2px solid #8B4513;
}

.card-footer .health,
.card-footer .attack {
    font-size: 18px;
    font-weight: bold;
    color: #2F1810;
    display: flex;
    align-items: center;
    gap: 4px;
}

.card-footer .health .icon {
    color: #DC143C;
}

.card-footer .attack .icon {
    color: #4169E1;
}
"""


def render_card_gallery_html(
    cards: list[Card], image_base_path: Path | None = None
) -> str:
    """Render multiple cards as an HTML gallery.

    Args:
        cards: List of cards to render.
        image_base_path: Base path for card images.

    Returns:
        Complete HTML document with card gallery.
    """
    card_html = "\n".join(
        render_card_html(card, image_base_path, include_image=True) for card in cards
    )

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CartesSociete - Card Gallery</title>
    <style>
        {get_card_css()}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #2F1810;
            padding: 20px;
            margin: 0;
        }}

        h1 {{
            color: #F5DEB3;
            text-align: center;
            margin-bottom: 30px;
        }}

        .gallery {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
        }}
    </style>
</head>
<body>
    <h1>CartesSociete - Card Gallery</h1>
    <div class="gallery">
        {card_html}
    </div>
</body>
</html>
"""


class CardRenderer:
    """High-level card renderer with configurable options."""

    def __init__(
        self,
        image_base_path: Path | None = None,
        ascii_width: int = 40,
    ) -> None:
        """Initialize the renderer.

        Args:
            image_base_path: Base path for card images.
            ascii_width: Width for ASCII rendering.
        """
        self.image_base_path = image_base_path
        self.ascii_width = ascii_width

    def to_ascii(self, card: Card) -> str:
        """Render card as ASCII art.

        Args:
            card: The card to render.

        Returns:
            ASCII representation of the card.
        """
        return render_card_ascii(card, self.ascii_width)

    def to_html(self, card: Card, include_image: bool = True) -> str:
        """Render card as HTML.

        Args:
            card: The card to render.
            include_image: Whether to include the card image.

        Returns:
            HTML representation of the card.
        """
        return render_card_html(card, self.image_base_path, include_image)

    def to_gallery_html(self, cards: list[Card]) -> str:
        """Render multiple cards as HTML gallery.

        Args:
            cards: List of cards to render.

        Returns:
            Complete HTML document with card gallery.
        """
        return render_card_gallery_html(cards, self.image_base_path)

    def save_gallery(self, cards: list[Card], output_path: Path) -> None:
        """Save a card gallery to an HTML file.

        Args:
            cards: List of cards to include.
            output_path: Path to save the HTML file.
        """
        html = self.to_gallery_html(cards)
        output_path.write_text(html, encoding="utf-8")
