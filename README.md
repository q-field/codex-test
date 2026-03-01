# Space Invaders (Pygame starter)

A from-scratch Space Invaders starter built with Pygame.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
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
