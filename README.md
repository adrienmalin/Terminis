# Terminis
Tetris clone for terminal. Ideal for servers without GUI!

## Installation

```bash
pip install --user terminis
```

## Usage

```bash
terminis [edit|n]
```
* edit: edit controls in text editor
* n (integer between 1 and 15): start at level n

## Controls edit

You can change keys by editing:
* `%appdata%\Terminis\config.cfg` on Windows
* `$XDG_CONFIG_HOME/Terminis/config.cfg` or `~/.config/Terminis/config.cfg` on Linux
