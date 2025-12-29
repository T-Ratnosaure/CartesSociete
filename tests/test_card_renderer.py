"""Tests for card renderer.

This module tests the CardRenderer class for rendering cards as ASCII or HTML.
"""

import pytest

from src.cards.models import (
    CardClass,
    CardType,
    ClassAbilities,
    CreatureCard,
    DemonCard,
    Family,
    FamilyAbilities,
    ScalingAbility,
    WeaponCard,
)
from src.cards.renderer import (
    CardRenderer,
    get_card_css,
    render_card_ascii,
    render_card_html,
)


@pytest.fixture
def sample_creature() -> CreatureCard:
    """Create a sample creature card for testing."""
    return CreatureCard(
        id="cyborg_lolo_le_gorille_1",
        name="Lolo le gorille",
        card_type=CardType.CREATURE,
        level=1,
        movement=1,
        family=Family.CYBORG,
        card_class=CardClass.BERSEKER,
        family_abilities=FamilyAbilities(
            scaling=[
                ScalingAbility(threshold=3, effect="invoque hydre steam"),
                ScalingAbility(threshold=6, effect="Invoque dragon steam"),
            ]
        ),
        class_abilities=ClassAbilities(
            scaling=[
                ScalingAbility(threshold=2, effect="+5 dgt / -2 PV"),
                ScalingAbility(threshold=4, effect="+10 dgt / -5 PV"),
            ]
        ),
        bonus_text="+4 ATQ si raccoon familly 2",
        health=3,
        attack=0,
        image_path="Cyborg lvl 1/Lolo le gorille.png",
    )


@pytest.fixture
def sample_weapon() -> WeaponCard:
    """Create a sample weapon card for testing."""
    return WeaponCard(
        id="arme_hache_runique",
        name="Hache Runique",
        card_type=CardType.WEAPON,
        level=None,
        movement=1,
        family=Family.ARME,
        card_class=CardClass.ARME,
        family_abilities=FamilyAbilities(
            passive="L'arme peut etre equipee sur n'importe quel monstre"
        ),
        class_abilities=ClassAbilities(),
        bonus_text="Ajoute l'ATQ et les PV au monstre equipe",
        health=1,
        attack=5,
        image_path="Hache runique.png",
        equip_restriction="n'importe quel monstre",
    )


@pytest.fixture
def sample_demon() -> DemonCard:
    """Create a sample demon card for testing."""
    return DemonCard(
        id="demon_demon_majeur",
        name="Demon Majeur",
        card_type=CardType.DEMON,
        level=None,
        movement=1,
        family=Family.DEMON,
        card_class=CardClass.DEMON,
        family_abilities=FamilyAbilities(passive="Un seul demon peut apparaitre"),
        class_abilities=ClassAbilities(
            passive="Les demons ne peuvent pas gagner de Bonus"
        ),
        bonus_text="10 dgt imblocable",
        health=10,
        attack=10,
        image_path="Demon Majeur.png",
        summon_cost=6,
    )


class TestRenderCardAscii:
    """Tests for ASCII card rendering."""

    def test_renders_creature_name(self, sample_creature: CreatureCard) -> None:
        """Test that creature name appears in ASCII output."""
        output = render_card_ascii(sample_creature)
        assert "Lolo le gorille" in output

    def test_renders_creature_stats(self, sample_creature: CreatureCard) -> None:
        """Test that creature stats appear in ASCII output."""
        output = render_card_ascii(sample_creature)
        assert "<3 3" in output  # Health
        assert "X 0" in output  # Attack

    def test_renders_creature_family_class(self, sample_creature: CreatureCard) -> None:
        """Test that family and class appear in ASCII output."""
        output = render_card_ascii(sample_creature)
        assert "Cyborg" in output
        assert "Berseker" in output

    def test_renders_creature_level(self, sample_creature: CreatureCard) -> None:
        """Test that level appears in ASCII output."""
        output = render_card_ascii(sample_creature)
        assert "(1)" in output

    def test_renders_weapon_level_x(self, sample_weapon: WeaponCard) -> None:
        """Test that weapon shows X for level."""
        output = render_card_ascii(sample_weapon)
        assert "(X)" in output

    def test_renders_abilities(self, sample_creature: CreatureCard) -> None:
        """Test that abilities appear in ASCII output."""
        output = render_card_ascii(sample_creature)
        assert "3: invoque hydre steam" in output
        assert "2: +5 dgt / -2 PV" in output

    def test_renders_bonus_text(self, sample_creature: CreatureCard) -> None:
        """Test that bonus text appears in ASCII output."""
        output = render_card_ascii(sample_creature)
        assert "+4 ATQ si raccoon familly 2" in output

    def test_custom_width(self, sample_creature: CreatureCard) -> None:
        """Test rendering with custom width."""
        output_40 = render_card_ascii(sample_creature, width=40)
        output_60 = render_card_ascii(sample_creature, width=60)

        # All lines should be the specified width
        for line in output_40.split("\n"):
            assert len(line) == 40, f"Line not 40 chars: {line!r}"

        for line in output_60.split("\n"):
            assert len(line) == 60, f"Line not 60 chars: {line!r}"


class TestRenderCardHtml:
    """Tests for HTML card rendering."""

    def test_renders_creature_html(self, sample_creature: CreatureCard) -> None:
        """Test basic HTML rendering of creature card."""
        html = render_card_html(sample_creature, include_image=False)

        assert '<div class="card creature level-1"' in html
        assert 'data-card-id="cyborg_lolo_le_gorille_1"' in html
        assert "Lolo le gorille" in html

    def test_renders_weapon_html(self, sample_weapon: WeaponCard) -> None:
        """Test basic HTML rendering of weapon card."""
        html = render_card_html(sample_weapon, include_image=False)

        assert '<div class="card weapon level-x"' in html
        assert "Hache Runique" in html

    def test_renders_demon_html(self, sample_demon: DemonCard) -> None:
        """Test basic HTML rendering of demon card."""
        html = render_card_html(sample_demon, include_image=False)

        assert '<div class="card demon level-x"' in html
        assert "Demon Majeur" in html

    def test_renders_stats(self, sample_creature: CreatureCard) -> None:
        """Test that stats appear in HTML output."""
        html = render_card_html(sample_creature, include_image=False)

        assert '<span class="health">' in html
        assert "3" in html  # Health
        assert '<span class="attack">' in html
        assert "0" in html  # Attack

    def test_renders_family_abilities(self, sample_creature: CreatureCard) -> None:
        """Test that family abilities appear in HTML output."""
        html = render_card_html(sample_creature, include_image=False)

        assert '<div class="family-abilities">' in html
        assert "invoque hydre steam" in html
        assert '<span class="threshold">3:</span>' in html

    def test_renders_class_abilities(self, sample_creature: CreatureCard) -> None:
        """Test that class abilities appear in HTML output."""
        html = render_card_html(sample_creature, include_image=False)

        assert '<div class="class-abilities">' in html
        assert "+5 dgt / -2 PV" in html

    def test_renders_passive_abilities(self, sample_weapon: WeaponCard) -> None:
        """Test that passive abilities appear in HTML output."""
        html = render_card_html(sample_weapon, include_image=False)

        assert '<div class="ability passive">' in html
        # Note: Apostrophe is HTML-escaped for XSS prevention
        assert "L&#x27;arme peut etre equipee" in html

    def test_renders_bonus_text(self, sample_creature: CreatureCard) -> None:
        """Test that bonus text appears in HTML output."""
        html = render_card_html(sample_creature, include_image=False)

        assert '<div class="bonus-text">' in html
        assert "+4 ATQ si raccoon familly 2" in html

    def test_includes_image_when_requested(self, sample_creature: CreatureCard) -> None:
        """Test that image is included when requested."""
        html_with_image = render_card_html(sample_creature, include_image=True)
        html_without_image = render_card_html(sample_creature, include_image=False)

        assert '<div class="card-image">' in html_with_image
        assert '<div class="card-image">' not in html_without_image


class TestGetCardCss:
    """Tests for CSS generation."""

    def test_returns_css_string(self) -> None:
        """Test that get_card_css returns a non-empty string."""
        css = get_card_css()
        assert isinstance(css, str)
        assert len(css) > 0

    def test_contains_card_class(self) -> None:
        """Test that CSS contains main card class."""
        css = get_card_css()
        assert ".card" in css

    def test_contains_level_classes(self) -> None:
        """Test that CSS contains level-specific classes."""
        css = get_card_css()
        assert ".card.level-1" in css
        assert ".card.level-2" in css

    def test_contains_type_classes(self) -> None:
        """Test that CSS contains type-specific classes."""
        css = get_card_css()
        assert ".card.weapon" in css or ".card.demon" in css


class TestCardRenderer:
    """Tests for CardRenderer class."""

    def test_to_ascii(self, sample_creature: CreatureCard) -> None:
        """Test CardRenderer.to_ascii method."""
        renderer = CardRenderer()
        output = renderer.to_ascii(sample_creature)

        assert "Lolo le gorille" in output

    def test_to_html(self, sample_creature: CreatureCard) -> None:
        """Test CardRenderer.to_html method."""
        renderer = CardRenderer()
        html = renderer.to_html(sample_creature, include_image=False)

        assert '<div class="card' in html

    def test_to_gallery_html(
        self,
        sample_creature: CreatureCard,
        sample_weapon: WeaponCard,
    ) -> None:
        """Test CardRenderer.to_gallery_html method."""
        renderer = CardRenderer()
        html = renderer.to_gallery_html([sample_creature, sample_weapon])

        assert "<!DOCTYPE html>" in html
        assert "Lolo le gorille" in html
        assert "Hache Runique" in html
        assert '<div class="gallery">' in html

    def test_custom_ascii_width(self, sample_creature: CreatureCard) -> None:
        """Test CardRenderer with custom ASCII width."""
        renderer = CardRenderer(ascii_width=50)
        output = renderer.to_ascii(sample_creature)

        for line in output.split("\n"):
            assert len(line) == 50
