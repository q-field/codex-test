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
- Restart after win/lose: `R`
- Quit: `Esc`

## Included MVP+

- Player movement and cooldown-based shooting
- Alien formation movement, edge bounce, and downward drop
- Alien speed scaling as enemies are defeated
- Random alien return fire
- Bullet collision handling (player bullets and alien bullets)
- Score, lives, start/win/lose states
