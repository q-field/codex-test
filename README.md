# Space Invaders (Pygame starter)

A from-scratch Space Invaders starter built with Pygame APIs.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python main.py
```

## macOS fix for `SDL.h file not found`

If `pip install pygame` tries to compile from source and fails with `SDL.h file not found`, use these steps:

1. Use Python 3.12 (3.13 may not have wheels for all pygame builds yet).
2. Upgrade pip/setuptools/wheel in your venv.
3. Install from `requirements.txt` (this project now uses `pygame-ce`, which ships prebuilt wheels on macOS more reliably).

Example:

```bash
brew install python@3.12
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python main.py
```

## Controls

- Move: `A/D` or `Left/Right`
- Shoot: `Space`
- Start game: `Enter` (or `Space` on start screen)
- Pause/resume: `P`
- Restart after win/lose: `R`
- Quit: `Esc`

## Included gameplay

- Smoothed player acceleration/deceleration for tighter movement feel
- Gentler per-wave speed scaling so progression stays beatable
- Invader firing from bottom-most survivors in each column (classic behavior)
- Destructible bunkers and pixel-style sprites inspired by original Space Invaders silhouettes
- Animated invader sprite frames + bonus UFO target worth extra points
- Explosion particle effects on alien/UFO/player hits
- Wave progression (`3` waves to win), plus score/lives/high-score HUD
- Persistent local high score saved to `high_score.json`
- Start / pause / win / lose states and restart flow
