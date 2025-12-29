"""Generate PDF version of CartesSociete game rules."""

from fpdf import FPDF


def generate_rules_pdf(output_path: str) -> None:
    """Generate the rules PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "CartesSociete", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 14)
    pdf.cell(0, 10, "Official Game Rules", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Helper functions
    def title(text: str) -> None:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    def bullet(text: str) -> None:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, f"    - {text}", new_x="LMARGIN", new_y="NEXT")

    def text(content: str) -> None:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, content, new_x="LMARGIN", new_y="NEXT")

    # Terminology
    title("Terminology")
    bullet("PO = Points d'Or (Cost/Gold Points)")
    bullet("PV = Points de Vie (Health Points)")
    pdf.ln(5)

    # Setup
    title("Game Setup")
    bullet("2-5 players")
    bullet("Each player starts with 400 PV")
    bullet("Each player starts with 0 cards in hand")
    bullet("Each card exists in 5 copies in the game")
    bullet("Shared market - all players buy from same cards")
    pdf.ln(5)

    # Card Acquisition
    title("Card Acquisition Rules")
    bullet("No draw phase - cards only acquired through market")
    bullet("You can ONLY buy Level 1 cards (never Level 2)")
    bullet("Level 2 cards only come from evolution")
    bullet("When discard pile is empty, shuffle it for new draw pile")
    pdf.ln(5)

    # Market Rules
    title("Market Rules")
    bullet("Buy as many cards as you can afford within PO limit")
    bullet("Turn order rotates every 2 turns (who buys first)")
    bullet("Unbought cards stay until next deck mixing")
    pdf.ln(5)

    # PO Progression
    title("PO Progression")
    text("2 turns per card cost level")
    text("Formula: card_cost x 2 + 1")
    pdf.ln(3)
    text("Turns 1-2:  Cost 1 cards = 3 PO (Turn 1 = 4 PO)")
    text("Turns 3-4:  Cost 2 cards = 5 PO")
    text("Turns 5-6:  Cost 3 cards = 7 PO")
    text("Turns 7-8:  Cost 4 cards = 9 PO")
    text("Turns 9-10: Cost 5 cards = 11 PO")
    pdf.ln(5)

    # Evolution
    title("Evolution Mechanic")
    bullet("Requirement: 3 cards with the exact same name")
    bullet("Cards are DOUBLE-SIDED (Level 1 front / Level 2 back)")
    bullet("Can happen on the board OR in hand")
    bullet("2 cards go to discard pile (recyclable)")
    bullet("1 card STAYS and is FLIPPED to Level 2 side (verso)")
    pdf.ln(5)

    # Deck Mixing
    title("Deck Mixing (after every even turn)")
    text("After Turn 2: Mix remaining into Cost-2 pile")
    text("After Turn 4: Mix remaining into Cost-3 pile")
    text("After Turn 6: Mix remaining into Cost-4 pile")
    text("After Turn 8: Mix remaining into Cost-5 pile")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Mixing Process:", new_x="LMARGIN", new_y="NEXT")
    bullet("1. Take remaining cards from current pile")
    bullet("2. Shuffle and split randomly (not symmetric)")
    bullet("3. Mix one half with next cost pile")
    bullet("4. Discard the other half")
    pdf.ln(5)

    # Board Limits
    title("Board Limits")
    bullet("Maximum 8 cards on board at any time")
    bullet("Play 1 card OR replace 1 card per turn (not both)")
    bullet("Exception: Lapin family can exceed 8-card limit")
    pdf.ln(5)

    # Combat
    title("Combat Resolution")
    bullet("Simultaneous - all players resolve at same time")
    bullet("Attack ALL opponents - hits every other player")
    bullet("Cards never die - stay on board permanently")
    bullet("Defense = HP (health stat on card)")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Combat Calculation (for each opponent):", new_x="LMARGIN", new_y="NEXT")
    bullet("1. Calculate total attack of your board")
    bullet("2. Calculate opponent's total HP (their defense)")
    bullet("3. Damage = Your Attack - Their Total HP")
    bullet("4. Opponent loses that much PV (if positive)")
    pdf.ln(5)

    # Win Condition
    title("Win Condition")
    bullet("When a player's PV reaches 0 or below: eliminated")
    bullet("Game continues until only 1 player remains")
    bullet("Last player standing wins!")

    # Save
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    generate_rules_pdf("data/rules/CartesSociete_Rules.pdf")
