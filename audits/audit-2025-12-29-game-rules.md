# Regulatory Audit Report - Game Rules

**Auditor**: Wealon, Regulatory Team
**Date**: 2025-12-29
**Scope**: Game Rules Documentation (game_rules_draft.md, CartesSociete_Rules.pdf, generate_rules_pdf.py)
**Verdict**: MAJOR

---

## Executive Summary

I have conducted a thorough examination of the CartesSociete game rules documentation, and I must say... I've seen better organization in a toddler's toy box. The rules contain multiple logical inconsistencies, glaring omissions, ambiguous language, and balance concerns that would make any playtester weep. The PDF generation script, while functional, faithfully reproduces all these problems - so at least it's consistently wrong.

As I've noted in seventeen previous audits of similar game documentation: "incomplete rules lead to heated arguments at the gaming table." Let us proceed with the enumeration of failures.

---

## Critical Issues

### CRIT-001: Formula vs. Table Contradiction (PO Progression)

**Location**: `game_rules_draft.md` lines 57-67

The stated formula `card_cost x 2 + 1` does NOT match the table:

| Turns | Market Cost | Formula Result | Stated in Table |
|-------|-------------|----------------|-----------------|
| 1-2   | Cost 1      | 1 x 2 + 1 = 3  | 3 PO (Turn 1 = 4 PO) - EXCEPTION |
| 3-4   | Cost 2      | 2 x 2 + 1 = 5  | 5 PO - CORRECT |
| 5-6   | Cost 3      | 3 x 2 + 1 = 7  | 7 PO - CORRECT |
| 7-8   | Cost 4      | 4 x 2 + 1 = 9  | 9 PO - CORRECT |
| 9-10  | Cost 5      | 5 x 2 + 1 = 11 | 11 PO - CORRECT |

**Issue**: Turn 1 has 4 PO as an exception, but Turn 2 should have 3 PO according to the formula. The table says "3 PO" for turns 1-2, then parenthetically "(Turn 1 = 4 PO)". This is AMBIGUOUS:
- Does Turn 2 have 3 PO or 4 PO?
- Why is Turn 1 exceptional?

**Severity**: CRITICAL - Core economy mechanics are unclear.

### CRIT-002: "5 Cards Flipped" Rule Never Defined

**Location**: `game_rules_draft.md` line 24-25

The rules state "Flip 5 cards of cost 1" but:
1. What happens when fewer than 5 cards remain in the pile?
2. Is this 5 cards per player or 5 cards total for the shared market?
3. Are these cards flipped at the start of EVERY turn or only when the market is empty?

**Impact**: Shared market mechanics are FUNDAMENTALLY UNDEFINED.

### CRIT-003: Missing Rules for Weapons and Demons

**Location**: Entire rules document

The rules mention NOTHING about:
- **Weapons**: How are weapons acquired? How are they equipped? The card data shows weapons with ATQ/PV that "add to equipped monster" but the rules are silent.
- **Demons**: The card data shows Invocateur class summons demons, but:
  - Where do demons come from?
  - Do they count toward the 8-card limit?
  - "Un seul demon peut apparaitre sur le plateau a la fois" - this is in the card data but NOT in the rules!

This is like publishing a chess rulebook that forgets to mention the queen.

### CRIT-004: "Cards Never Die" vs. "Sacrifice" Contradiction

**Location**: `game_rules_draft.md` line 77 vs. card data

Rules state: "Cards never die - they stay on board permanently"

BUT card data shows:
- `Diplo-Terre`: "sacrifier une carte a la fin du tour"
- `Licorne` (Level 1): "si 3 monture, sacrifier cette carte apres activation"
- `Mutanus empoisonne`: Self-damage effect

**Question**: Can cards be sacrificed? Where do sacrificed cards go? Is this different from "dying"?

---

## Major Issues

### MAJ-001: Turn 2 PO Ambiguity

The rules state Turn 1 = 4 PO, but what about Turn 2? The table implies:
- Turns 1-2 have Cost 1 cards with "3 PO (Turn 1 = 4 PO)"

This could mean:
- Turn 1 = 4 PO, Turn 2 = 3 PO (inconsistent within same phase)
- Turn 1 = 4 PO, Turn 2 = 4 PO (then why mention 3 PO at all?)

PDF generation script at line 71 faithfully reproduces this confusion:
```python
text("Turns 1-2:  Cost 1 cards = 3 PO (Turn 1 = 4 PO)")
```

### MAJ-002: Deck Mixing Process is Vague and Wasteful

**Location**: `game_rules_draft.md` lines 50-54

The mixing process states:
1. Take remaining cards
2. "Shuffle and split randomly (not symmetric)"
3. Mix ONE HALF with next cost pile
4. "Discard the other half"

**Issues**:
- "Not symmetric" - what does this mean? Random split ratios? 60/40? 70/30?
- HALF THE CARDS ARE DISCARDED? This seems like a massive card loss mechanism that is never explained or justified.
- Where do discarded cards go? To the discard pile (recyclable) or removed from game?

### MAJ-003: Evolution Mechanic - Location Ambiguity

**Location**: `game_rules_draft.md` lines 34-38

"Can happen on the board OR in hand"

But:
- If evolution happens in hand, when can it be triggered?
- If 3 cards are on board and you evolve, do you now have 1 Level 2 card on board (net -2 board presence)?
- Can you evolve during combat? During your turn only? At any time?
- The 2 discarded cards - are they Level 1 or Level 2 side when discarded?

### MAJ-004: "Replace" Action Undefined

**Location**: `game_rules_draft.md` line 26, 71

"Play 1 card OR replace 1 card per turn (not both)"

What does "replace" mean?
- Remove a card from board and play a new one from hand?
- Where does the removed card go? Discard pile? Hand?
- Can you replace a Level 2 card with a Level 1 card?

### MAJ-005: Combat Resolution Timing

**Location**: `game_rules_draft.md` lines 79-84

"Each turn, after all players have played" - but when exactly?

1. All players take their market purchase actions simultaneously?
2. All players play their single card simultaneously?
3. THEN combat happens?
4. What about effects that trigger "per turn" - do they happen before or after combat?

### MAJ-006: Class Ability Thresholds - What Counts?

The Archer class ability says "+4 dgt si 2 defenseurs" - does this mean:
- YOUR 2 defenders?
- OPPONENT'S 2 defenders?
- Either? Both?

Similar ambiguity exists for many class abilities.

### MAJ-007: Lapin Family Exception is Vague

**Location**: `game_rules_draft.md` line 72

"Exception: Lapin family can exceed 8-card limit"

But the card data shows:
- `Lapincruste` (Level 1): "Le joueur peut poser 2 lapins supplementaires en jeu"
- `Lapincruste` (Level 2): "Le joueur peut poser 4 lapins supplementaires en jeu"
- Family ability at threshold 3: "+1 cartes sur le plateau"
- Family ability at threshold 5: "+2 cartes sur le plateau"

So the limit increases are SPECIFIC and STACKING, not just "can exceed." The rules grossly oversimplify this.

---

## Minor Issues

### MIN-001: Inconsistent Terminology

| Term in Rules | Term in Card Data | Issue |
|---------------|-------------------|-------|
| HP | PV (Points de Vie) | Used interchangeably |
| Defense | HP | Rules say "Defense = HP" but then use both |
| PO | Cost / Points d'Or / Gold | Multiple terms |
| "dgt" | "dommage" / "damage" | Abbreviated inconsistently |

### MIN-002: What Happens After Turn 10?

The PO progression table stops at Turn 10 (Cost 5 cards = 11 PO). What happens on Turn 11+?
- Does the game continue at Cost 5 / 11 PO forever?
- Is there a maximum turn count?
- What happens when the Cost 5 pile is exhausted?

### MIN-003: "Imblocable" Damage Undefined in Rules

Card data frequently references "dgt imblocable" (unblockable damage) and the Nature family scales with it. The rules NEVER DEFINE what this means:
- Does it bypass HP/Defense calculation?
- Does it go directly to player PV?
- Can it be reduced by any means?

### MIN-004: Market Refill Undefined

"Flip 5 cards of cost 1" at start - but what happens when players buy some cards?
- Are new cards flipped immediately to replace bought cards?
- Or does the market stay depleted until next turn?
- Or until next "deck mixing" event?

### MIN-005: Turn Order Rotation Mechanics

"Turn order rotates every 2 turns (determines who buys first)"

- How exactly? Clockwise? Counterclockwise?
- Does the player who went LAST now go FIRST? Or shift by one position?
- Example with 4 players would help immensely.

### MIN-006: PDF Script Missing Information

The PDF generation script (`generate_rules_pdf.py`) is missing several pieces of information from the markdown:
- Does not mention "Each card exists in 5 copies in the game" (line 48 mentions it, but it's from markdown)
- Missing the "Draft rules - pending review" footer
- No version number on the PDF

### MIN-007: Starting Hand Clarity

"Each player starts with 0 cards in hand" - This is stated, but then:
- Players buy cards in Turn 1
- Do bought cards go to hand or directly to board?
- The "Play 1 card" action implies cards are in hand first

---

## Balance Concerns

### BAL-001: Lapin Family is Potentially Overpowered

The Lapin family can:
1. Exceed the 8-card board limit (unique ability)
2. Get +2 ATQ for all lapins at threshold 8
3. Stack multiple board limit increases from Lapincruste AND family abilities

With 8 Lapins + potentially +4 more from Lapincruste Level 2 + family threshold bonuses, Lapins could have 12+ cards on board while opponents are capped at 8.

**Recommendation**: Needs simulation testing IMMEDIATELY.

### BAL-002: Nature Family Unblockable Damage Scaling

Nature family gets:
- Threshold 2: 2 unblockable damage
- Threshold 4: 5 unblockable damage
- Threshold 6: 8 unblockable damage

If this BYPASSES the normal "Your Attack - Their Total HP" calculation, it's free damage every turn. With 400 starting PV, that's only 50 turns at threshold 6 to win through unblockable alone.

### BAL-003: Demon Summon Limits Contradict Rules

Card data: "Un seul demon peut apparaitre sur le plateau a la fois" (Only one demon can appear on the board at a time)

But with multiple Invocateurs at threshold 6, can you summon multiple Demon Majeurs? The rule says "un seul" but the class ability says "invoque un demon majeur" - these potentially conflict.

### BAL-004: First-Player Advantage

- Turn 1 first player gets 4 PO to buy from fresh market
- By the time last player buys, market may be depleted of best cards
- With 5 players, this could be significant

Turn order rotation every 2 turns helps, but doesn't fully address Turn 1 advantage.

### BAL-005: Exponential HP Scaling

The combat formula "Your Attack - Their Total HP" means:
- High HP builds become increasingly stronger
- Defense stacking may become dominant strategy
- Needs Monte Carlo simulation to verify

---

## Code Quality Issues in PDF Generator

### CQ-001: No Error Handling
```python
def generate_rules_pdf(output_path: str) -> None:
    pdf = FPDF()
    ...
    pdf.output(output_path)
```

No try/except around file operations. What if path doesn't exist? What if permission denied?

### CQ-002: Hardcoded Magic Numbers
```python
pdf.set_font("Helvetica", "B", 24)  # Why 24?
pdf.cell(0, 15, "CartesSociete", ...)  # Why 15?
pdf.ln(10)  # Why 10?
```

Per CLAUDE.md: "NEVER hardcode game values (use configs)"

### CQ-003: Missing Docstrings on Helper Functions

The nested functions `title()`, `bullet()`, and `text()` have no docstrings. Per CLAUDE.md, docstrings are REQUIRED for public APIs (and these are effectively the internal API of this module).

### CQ-004: Relative Path in Main Block
```python
if __name__ == "__main__":
    generate_rules_pdf("data/rules/CartesSociete_Rules.pdf")
```

This assumes the script is run from the repository root. Should use `Path(__file__).parent.parent / "data/rules/..."` or accept path as argument.

---

## Missing Rules Summary (Items Not Covered)

1. **Weapon acquisition and equipment** - How do players get and use weapons?
2. **Demon summoning mechanics** - Full details needed
3. **Spell mechanics** - Mages "cast spells" but spells are never defined
4. **"Sorts" (spells) damage calculation** - How does spell damage work?
5. **Buff/debuff stacking** - Do multiple "+ATQ" effects stack? Additively? Multiplicatively?
6. **Timing of "per turn" effects** - Beginning of turn? End? During?
7. **Tie-breaking rules** - What if two players reach 0 PV simultaneously?
8. **Forfeit/disconnect rules** - What if a player leaves?
9. **S-Team cards** - Card model shows S-Team class with "level X" but rules never mention
10. **Hall of Win family** - Cards exist in data but family ability not documented

---

## Recommendations (REQUIRED FIXES)

1. **IMMEDIATELY** clarify Turn 1/Turn 2 PO values with explicit statement for each turn
2. **ADD** complete weapon acquisition and equipment rules section
3. **ADD** complete demon summoning rules section
4. **DEFINE** "unblockable damage" and how it interacts with combat
5. **CLARIFY** "replace" action mechanics
6. **SPECIFY** market refill rules
7. **ADD** timing chart for turn phases
8. **DEFINE** evolution timing and location rules
9. **CLARIFY** what "cards never die" means vs. sacrifice mechanics
10. **ADD** examples for complex mechanics
11. **RUN** balance simulations for Lapin and Nature families
12. **FIX** PDF generator to use config values instead of hardcoded numbers
13. **ADD** error handling to PDF generator
14. **ADD** version number to both markdown and PDF rules

---

## Document Discrepancies

### Markdown vs. PDF Differences

The PDF accurately reproduces the markdown content, but both contain the same errors. The PDF does NOT include:
- The table formatting from markdown (it's converted to plain text)
- The "Draft rules - pending review" footer
- Any indication this is not final

---

## Auditor's Notes

I have spent considerable time reviewing what amounts to a half-finished ruleset that someone decided to generate a "professional-looking" PDF from. The PDF looks nice. The content is incomplete. It's like putting lipstick on a pig, except the pig is also missing a leg.

The card data JSON files are actually more complete than the rules document itself - I had to read the card data to understand mechanics that the rules never bothered to explain. This is BACKWARDS. The rules should be the source of truth, with cards implementing those rules.

As I noted in my previous audit of this codebase (audit-2025-12-29-card-system.md), there appear to be systemic issues with documentation completeness. I recommend a full documentation review before ANY public release.

Per regulatory requirements, this audit must be addressed within 14 days. I will be scheduling a follow-up review.

**I'll be watching.**

---

*Audit completed at 2025-12-29 by Wealon, Regulatory Team*
*Next scheduled audit: 2026-01-12*
