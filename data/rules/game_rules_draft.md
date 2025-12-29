# CartesSociete - Game Rules (Draft)

## Terminology
- **PO** = Cost (Points d'Or)
- **PV** = Health Points (Points de Vie)

## Setup
- **2-5 players**
- Each player starts with **400 PV**
- Each player starts with **0 cards in hand**
- Each card exists in **5 copies** in the game
- **Shared market** - all players buy from the same revealed cards

## Card Acquisition Rules
- **No draw phase** - cards only acquired through market
- **You can ONLY buy Level 1 cards** (never Level 2)
- Level 2 cards only come from **evolution**
- When the discard pile is empty, shuffle it to form a new draw pile

## Turn Structure

### Turns 1-2: Starting Phase
- Players have **4 PO** (Turn 1) / **5 PO** (Turn 2)
- Flip 5 cards of cost 1
- **Buy as many cards as you can afford** within PO limit
- **Play 1 card OR replace 1 card** (not both)

### Market Rules
- **Turn order rotates every 2 turns** (determines who buys first)
- **Unbought cards stay** in market until next deck refill/mixing
- All players buy from the **same shared market**

### Evolution Mechanic
- **Requirement**: 3 cards with the **exact same name**
- **Result**: 1 Level 2 card of the **same name**
- Can happen on the board OR in hand
- 2 cards go to **discard pile** (recyclable)
- 1 card is **removed from game** (exile)

### Deck Mixing (after every even turn)
After each even turn, mix remaining cards into higher cost pile:

| After Turn | Mix remaining into |
|------------|-------------------|
| 2 | Cost-2 pile |
| 4 | Cost-3 pile |
| 6 | Cost-4 pile |
| 8 | Cost-5 pile |

**Mixing process:**
1. Take remaining cards from current pile
2. Shuffle and split randomly (not symmetric)
3. Mix one half with next cost pile
4. Discard the other half

## PO Progression
- **Turn 1**: 4 PO (fixed)
- **Turn 2+**: `turn × 2 + 1`

| Turn | PO |
|------|-----|
| 1 | 4 |
| 2 | 5 |
| 3 | 7 |
| 4 | 9 |
| 5 | 11 |
| 6 | 13 |
| 7 | 15 |
| 8 | 17 |
| 9 | 19 |

## Board Limits
- **Maximum 8 cards on board** at any time
- **Play 1 card OR replace 1 card** per turn (not both)
- Exception: Lapin family can exceed 8-card limit (card-specific ability)

## Combat Resolution
- **Simultaneous combat** - all players resolve at the same time
- **Attack ALL opponents** - your attack hits every other player
- **Cards never die** - they stay on board permanently
- **Defense = HP** (health stat on card)
- Each turn, after all players have played:
  1. Calculate **total attack** of your board
  2. For **each opponent**: Calculate their **total HP** (defense)
  3. **Damage to each opponent = Your Attack - Their Total HP**
  4. Each opponent loses that much PV (if positive)

## Win Condition
- When a player's PV reaches **0 or below**, they are **eliminated**
- Game continues until **only 1 player remains**
- Last player standing **wins**

---

*Draft rules - pending review*
