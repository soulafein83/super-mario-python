# Super Mario Python — Project Review, Findings & Recommendations

> This document summarizes the work completed so far in this repository, records
> technical findings from a full review of the codebase, and lists prioritized
> recommendations for future work. Written entirely in English.

---

## 1. Project Overview

This is a **data-driven Python/pygame reimplementation of Super Mario Bros**,
inspired by Meth-Meth-Method's project. It runs at a fixed **640×480** window at
60 FPS on a **32×32 tile grid** (20 tiles wide × 15 visible rows).

```
main.py                 # game loop + scene orchestration (menu → level)
compile.py              # py2exe standalone packaging
requirements.txt        # pygame==2.0.0.dev10, scipy==1.4.1
classes/                # engine core
  Dashboard, Camera, Input, Level, Maths, Menu, Pause, Sound,
  Sprite, Sprites, Spritesheet, Tile, Animation, GaussianBlur
entities/               # gameplay objects (all extend EntityBase)
  Mario, Goomba, Koopa, Mushroom (RedMushroom), Coin, CoinBox,
  CoinBrick, RandomBox, Item, EntityBase
traits/                 # behavior mixins injected as a dict per entity
  jump, go, leftrightwalk, bounce
sprites/*.json          # sprite-sheet → Sprite definitions
levels/*.json           # data-driven level layout + entity spawns
img/, sfx/              # assets
```

---

## 2. Architecture & Implemented Features

### Rendering pipeline
- `Spritesheet` loads a PNG/GIF, sets a black colorkey for transparency, and slices
  frames via `image_at`.
- `Sprites.loadSprites` reads each JSON (`background`, `animation`, `character`,
  `item`) into a flat collection of `Sprite` objects — static images or animated
  frame sequences.
- Tiles are drawn by iterating the level grid with camera offset; sprites use
  per-frame `Animation.update()` timing. The font is rendered from a character-grid
  sprite sheet (no TTF dependency).

### Data-driven levels
Each JSON defines `objects` (bush/cloud/pipe), `layers` (sky/ground extents),
`entities` (CoinBox, Goomba, Koopa, coin, coinBrick, RandomBox) and a top-level
`length`. `Level.loadLevel` builds the tile grid, decorates it with sprites, and
spawns entities.

### Movement via traits
Each entity holds a `traits` dict; `EntityBase.updateTraits()` ticks every trait:
- **GoTrait** — acceleration/deceleration, max speed, boost (Shift), heading/flips,
  idle/run/jump sprite selection.
- **JumpTrait** — gravity + variable jump height using a custom deacceleration
  formula (`deaccelerationHeight`) so jumps always reach apex regardless of hold time.
- **LeftRightWalkTrait** — AI mob horizontal patrol.
- **bounceTrait** — stomp bounce response.

### Collision
Two systems work together:
1. **Collider** — tile-grid resolution in two passes (X then Y) for axis-separated
   separation, plus level-border clamping.
2. **EntityCollider.check()** — returns a `CollisionState(isColliding, isTop)` via
   point-in-rect tests (`determineSide`). Mario/mobs use this to decide stomp vs side
   collision.

### Game state & entities
- Menu (level select + settings with persisted music/SFX in `settings.json`),
  gameplay, pause (Gaussian-blur overlay via scipy), and death animation (synchronous
  expanding-circle sequence).
- Power-up system: small/big (`powerUpState` 0/1) with invincibility-frame flicker.
- Enemies: Goomba stomp, Koopa shell (spawn → sleep → kick bounce), red mushroom
  power-up, coin blocks/bricks that spawn a bouncing `Item`.

---

## 3. Technical Observations & Issues Found

| # | Area | Observation |
|---|------|-------------|
| 1 | Dependencies | `requirements.txt` pins `pygame==2.0.0.dev10` and `scipy==1.4.1`. The environment is **Python 3.14** with no pygame installed — these old versions are incompatible, so the game cannot currently be launched as-is. |
| 2 | Working tree | 10 files show uncommitted changes (line-ending/whitespace normalization). No `.editorconfig`; risk of CRLF/LF noise on every commit. |
| 3 | Error handling | `Collider`, `Level.drawLevel` and several `add*` methods use bare `except Exception / except IndexError` to silently bail — this hides real bugs (e.g., out-of-range tile access). |
| 4 | Collision math | Coordinate bug in `determineSide`: `(rect1.midleft[0] / 2, rect1.midleft[1] / 2)` divides world coordinates by 2 erroneously; side classification is unreliable. |
| 5 | Constructor order | Inconsistent mob coordinate handling: Goomba uses `super().__init__(y, x - 1, ...)`, Koopa `super().__init__(y - 1, x, ...)`, Mushroom `super().__init__(y, x - 1, ...)` — inconsistent placement math. |
| 6 | Input latency | In `Mario.update()` input is read *after* gravity/collision each frame (one-frame delay); physics then runs with the prior frame's intent. |
| 7 | Duplication | Goomba and RedMushroom share near-identical update/death/blit logic; could be a shared base class. Koopa differs enough to stay separate. |
| 8 | Win condition | No real level-complete/flagpole trigger; the "end" is only implied by the right level-border clamp in `Collider.rightLevelBorderReached`. |
| 9 | Asset paths | `Sprites.__init__` hardcodes `"./sprites/*.json"`, so running from a different working directory breaks sprite loading. `Level`/`Menu` already accept `base_dir`; not all call sites do. |
| 10 | Dead/hardcoded | `Tile.drawRect()` (red debug box) is unused; sound volumes hardcoded to 0.2; string style oscillates between `.format()` and f-strings (commits keep reverting). |

---

## 4. Future Recommendations (prioritized)

### P0 — Make the project runnable
1. Update `requirements.txt` for modern Python / pygame / numpy / scipy, add a venv
   note or `pyproject.toml`, and verify launch on this machine.

### P1 — Correctness & robustness
2. Fix the `/2` coordinate bug in `determineSide`.
3. Standardize mob constructor coordinate order (unify Goomba/Koopa/Mushroom).
4. Replace broad bare-excepts with targeted handling/logging; stop swallowing tile-
   index errors in `Level`.

### P2 — Features & gameplay
5. Add a proper level-complete/flagpole state instead of relying on the border clamp.

### P3 — Refactoring & maintainability
6. Refactor shared entity logic (Goomba/Mushroom) into a common mob base.
7. Harden asset paths with a single resolved BASE_DIR for sprites/audio/levels, so the
   game runs from any working directory.
8. Reduce input latency by reading input at frame start, before physics.
9. Clean dead code (`Tile.drawRect`), unify string style, add a headless smoke test for
   level-load and collision.

---

## 5. Housekeeping
- Normalize line endings across the repo and add an `.editorconfig`.
- Commit the current working-tree changes (they are currently uncommitted).
