# Terminis
Tetris clone for terminal. Ideal for servers without GUI!

## Installation

```bash
pip install --user terminis
```

## Usage
```bash
  terminis [level]
```
  level: integer between 1 and 15

## Controls edit

You can change keys by editing:
* `%appdata%\Terminis\config.cfg` on Windows
* `~/.local/share/Terminis/config.cfg` on Linux

Acceptable values:
* printable characters ('q', '*', ' '...)
* curses's constants name starting with "KEY_" (see [Python documentation](https://docs.python.org/3/library/curses.html?highlight=curses#constants))