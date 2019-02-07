# Terminis
Another Tetris clone... again... but for terminal. Ideal for servers without GUI!

## Screenshot
```bash
┌────────────HOLD───────────┐┌────────────────────┐┌────────────NEXT───────────┐
│                           ││                    ││                           │
│                           ││                    ││                           │
│                           ││                    ││                           │
│                           ││                    ││                           │
└───────────────────────────┘│                    │└───────────────────────────┘
┌────────────STATS──────────┐│                    │┌──────────CONTROLS─────────┐
│                           ││                    ││                           │
│ SCORE 0                   ││                    ││ LEFT  MOVE LEFT           │
│ HIGH  217812              ││                    ││ RIGHT MOVE RIGHT          │
│ TIME  00:00:01            ││                    ││ DOWN  SOFT DROP           │
│ LEVEL 1                   ││                    ││ SPACE HARD DROP           │
│ GOAL  5                   ││                    ││ UP    ROTATE COUNTER      │
│ LINES 0                   ││                    ││ *     ROTATE CLOCKWISE    │
│                           ││                    ││ H     HOLD                │
│                           ││                    ││ P     PAUSE               │
│                           ││                    ││ Q     QUIT                │
│                           ││                    ││                           │
│                           ││                    ││                           │
│                           ││                    ││                           │
│                           ││                    ││                           │
└───────────────────────────┘└────────────────────┘└───────────────────────────┘
```

## Usage
```bash
  python terminis.py [level]
```
  level: integer between 1 and 15
  
## Dependency
* Python
* Python module Curses (native on linux)

Can be installed on windows with:
```batch
  pip install --users windows-curses
```

## Controls edit
Edit values of dictionary CONTROLS in the script:
```python
CONTROLS = {
    "MOVE LEFT": "KEY_LEFT",
    "MOVE RIGHT": "KEY_RIGHT",
    "SOFT DROP": "KEY_DOWN",
    "HARD DROP": " ",
    "ROTATE COUNTER": "KEY_UP",
    "ROTATE CLOCKWISE": "*",
    "HOLD": "h",
    "PAUSE": "p",
    "QUIT": "q"
}
```
Acceptable values are printable keys ('q', 'w'...) and curses's constants name starting with "KEY_" (see [Python documentation](https://docs.python.org/3/library/curses.html?highlight=curses#constants))