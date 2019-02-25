# -*- coding: utf-8 -*-

from .pytetris import Tetris, Mino, Point

import sys

try:
    import curses
except ImportError:
    sys.exit(
"""This program requires curses.
You can install it on Windows with:
pip install --user windows-curses"""
    )
else:
    curses.COLOR_ORANGE = 8
    
import sched
import time
import os
import locale
import subprocess

try:
    import configparser
except ImportError: # Python2
    import ConfigParser as configparser


DIR_NAME = "Terminis"
HELP_MSG = """terminis [options]

Tetris clone for terminal

  --help\tshow command usage (this message)
  --edit\tedit controls in text editor
  --reset\treset to default controls settings
  --level=n\tstart at level n (integer between 1 and 15)"""


class Scheduler(sched.scheduler, dict):
    def __init__(self):
        sched.scheduler.__init__(self, time.time, time.sleep)
        dict.__init__(self)
        
    def repeat(self, name, delay, action, args=tuple()):
        self[name] = sched.scheduler.enter(self, delay, 1, self._repeat, (name, delay, action, args))
        
    def _repeat(self, name, delay, action, args):
        del(self[name])
        self.repeat(name, delay, action, args)
        action(*args)
        
    def single_shot(self, name, delay, action, args=tuple()):
        self[name] = sched.scheduler.enter(self, delay, 1, self._single_shot, (name, action, args))
        
    def _single_shot(self, name, action, args):
        del(self[name])
        action(*args)
        
    def cancel(self, name):
        if name in self:
            try:
                sched.scheduler.cancel(self, self.pop(name))
            except:
                sys.exit(name)


scheduler = Scheduler()


class Window:
    MINO_COLOR = {
        Mino.O: 0,
        Mino.I: 0,
        Mino.T: 0,
        Mino.L: 0,
        Mino.J: 0,
        Mino.S: 0,
        Mino.Z: 0
    }
    
    def __init__(self, game, width, height, begin_x, begin_y):
        self.game = game
        self.window = curses.newwin(height, width, begin_y, begin_x)
        if self.TITLE:
            self.title_begin_x = (width-len(self.TITLE)) // 2 + 1
        self.piece = None

    def draw_border(self):
        self.window.erase()
        self.window.border()
        if self.TITLE:
            self.window.addstr(0, self.title_begin_x, self.TITLE, curses.A_BOLD)

    def draw_piece(self, piece, position):
        if piece:
            if piece.prelocked:
                attr = self.MINO_COLOR[piece.MINOES_TYPE] | curses.A_BLINK | curses.A_REVERSE
            else:
                attr = self.MINO_COLOR[piece.MINOES_TYPE]
            for mino_position in piece.minoes_positions:
                position = mino_position + position
                self.draw_mino(position.x, position.y, attr)

    def draw_mino(self, x, y, attr):
        if y >= 0:
            self.window.addstr(y, x*2+1, "██", attr)


class Matrix(Window):
    NB_COLS = 10
    NB_LINES = 21
    WIDTH = NB_COLS*2+2
    HEIGHT = NB_LINES+1
    TITLE = ""

    def __init__(self, game, begin_x, begin_y):
        begin_x += (game.WIDTH - self.WIDTH) // 2
        begin_y += (game.HEIGHT - self.HEIGHT) // 2
        self.cells = [
            [None for x in range(self.NB_COLS)]
            for y in range(self.NB_LINES)
        ]
        self.piece = None
        Window.__init__(self, game, self.WIDTH, self.HEIGHT, begin_x, begin_y)

    def refresh(self, paused=False):
        self.draw_border()
        if paused:
            self.window.addstr(11, 9, "PAUSE", curses.A_BOLD)
        else:
            for y, line in enumerate(self.cells):
                for x, color in enumerate(line):
                    if color is not None:
                        self.draw_mino(x, y, color)
            self.draw_piece(self.game.current_piece, self.game.current_piece.position)
        self.window.refresh()


class HoldNext(Window):
    HEIGHT = 6
    PIECE_POSITION = Point(6, 3)

    def __init__(self, game, width, begin_x, begin_y):
        Window.__init__(self, game, width, self.HEIGHT, begin_x, begin_y)


class Hold(HoldNext):
    TITLE = "HOLD"

    def refresh(self, paused=False):
        self.draw_border()
        if not paused:
            self.draw_piece(self.game.held_piece, self.PIECE_POSITION)
        self.window.refresh()


class Next(HoldNext):
    TITLE = "NEXT"

    def refresh(self, paused=False):
        self.draw_border()
        if not paused:
            self.draw_piece(self.game.next_queue[0], self.PIECE_POSITION)
        self.window.refresh()


class Stats(Window):
    TITLE = "STATS"
    FILE_NAME = ".high_score"
    if sys.platform == "win32":
        DIR_PATH = os.environ.get("appdata", os.path.expanduser("~\Appdata\Roaming"))
    else:
        DIR_PATH = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    DIR_PATH = os.path.join(DIR_PATH, DIR_NAME)
    FILE_PATH = os.path.join(DIR_PATH, FILE_NAME)

    def __init__(self, game, width, height, begin_x, begin_y):
        self.width = width
        self.height = height
        try:
            with open(self.FILE_PATH, "r") as f:
               self.high_score = int(f.read())
        except:
            self.high_score = 0
        Window.__init__(self, game, width, height, begin_x, begin_y)

    def refresh(self):
        self.draw_border()
        self.window.addstr(2, 2, "SCORE\t{:n}".format(self.game.score))
        if self.game.score >= self.game.high_score:
            self.window.addstr(3, 2, "HIGH\t{:n}".format(self.game.high_score), curses.A_BLINK|curses.A_BOLD)
        else:
            self.window.addstr(3, 2, "HIGH\t{:n}".format(self.game.high_score))
        self.window.addstr(5, 2, "LEVEL\t%d" % self.game.level)
        self.window.addstr(6, 2, "GOAL\t%d" % self.game.goal)
        self.refresh_time()
        
    def refresh_time(self):
        t = time.localtime(time.time() - self.game.time)
        self.window.addstr(4, 2, "TIME\t%02d:%02d:%02d" % (t.tm_hour-1, t.tm_min, t.tm_sec))
        self.window.refresh()

    def save(self):
        if not os.path.exists(self.DIR_PATH):
            os.makedirs(self.DIR_PATH)
        try:
            with open(self.FILE_PATH, mode='w') as f:
                f.write(str(self.high_score))
        except Exception as e:
            print("High score could not be saved:")
            print(e)


class ControlsParser(configparser.SafeConfigParser):
    FILE_NAME = "config.cfg"
    if sys.platform == "win32":
        DIR_PATH = os.environ.get("appdata", os.path.expanduser("~\Appdata\Roaming"))
    else:
        DIR_PATH = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    DIR_PATH = os.path.join(DIR_PATH, DIR_NAME)
    FILE_PATH = os.path.join(DIR_PATH, FILE_NAME)
    SECTION = "CONTROLS"
    COMMENT = """# You can change key below.
# Acceptable values are:
# `SPACE`, `TAB`, `ENTER`,
# printable characters (`q`, `*`...) (case sensitive),
# curses's constants name starting with `KEY_`
# See https://docs.python.org/3/library/curses.html?highlight=curses#constants

"""
    DEFAULTS = {
        "MOVE LEFT": "KEY_LEFT",
        "MOVE RIGHT": "KEY_RIGHT",
        "SOFT DROP": "KEY_DOWN",
        "HARD DROP": "SPACE",
        "ROTATE CLOCKWISE": "ENTER",
        "ROTATE COUNTER": "KEY_UP",
        "HOLD": "h",
        "PAUSE": "p",
        "QUIT": "q"
    }

    def __init__(self):
        configparser.SafeConfigParser.__init__(self)
        self.optionxform = str
        self.add_section(self.SECTION)
        for action, key in self.DEFAULTS.items():
            self[action] = key

        if not os.path.exists(self.FILE_PATH):
            self.reset()

    def __getitem__(self, key):
        return self.get(self.SECTION, key)

    def __setitem__(self, key, value):
        self.set(self.SECTION, key, value)

    def reset(self):
        if not os.path.exists(self.DIR_PATH):
            os.makedirs(self.DIR_PATH)
        try:
            with open(self.FILE_PATH, 'w') as f:
                f.write(self.COMMENT)
                self.write(f)
        except Exception as e:
            print("Configuration could not be saved:")
            print(e)

    def edit(self):
        if sys.platform == "win32":
            try:
                subprocess.call(["edit.com", self.FILE_PATH])
            except FileNotFoundError:
                subprocess.call(["notepad.exe", self.FILE_PATH])
        else:
            os.system("${EDITOR:-nano}"+" "+self.FILE_PATH)


class ControlsWindow(Window, ControlsParser):
    TITLE = "CONTROLS"

    def __init__(self, game, width, height, begin_x, begin_y):
        ControlsParser.__init__(self)
        self.read(self.FILE_PATH)
        Window.__init__(self, game, width, height, begin_x, begin_y)
        self.refresh()
        for action, key in self.items(self.SECTION):
            if key == "SPACE":
                self[action] = " "
            elif key == "ENTER":
                self[action] = "\n"
            elif key == "TAB":
                self[action] = "\t"

    def refresh(self):
        self.draw_border()
        for y, (action, key) in enumerate(self.items("CONTROLS"), start=2):
            key = key.replace("KEY_", "").upper()
            self.window.addstr(y, 2, "%s\t%s" % (key, action.upper()))
        self.window.refresh()


class Game(Tetris):
    WIDTH = 80
    HEIGHT = Matrix.HEIGHT
    MINO_COLOR = {
        Mino.O: curses.COLOR_YELLOW,
        Mino.I: curses.COLOR_CYAN,
        Mino.T: curses.COLOR_MAGENTA,
        Mino.L: curses.COLOR_ORANGE,
        Mino.J: curses.COLOR_BLUE,
        Mino.S: curses.COLOR_GREEN,
        Mino.Z: curses.COLOR_RED
    }
    
    HIGH_SCORE_FILE_NAME = ".high_score"
    if sys.platform == "win32":
        DATA_DIR_PATH = os.environ.get("appdata", os.path.expanduser("~\Appdata\Roaming"))
    else:
        DATA_DIR_PATH = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    DATA_DIR_PATH = os.path.join(DATA_DIR_PATH, DIR_NAME)
    HIGH_SCORE_FILE_PATH = os.path.join(DATA_DIR_PATH, HIGH_SCORE_FILE_NAME)
    
    def __init__(self, scr):
        try:
            with open(self.HIGH_SCORE_FILE_PATH, "r") as f:
               high_score = int(f.read())
        except:
            high_score = 0
        Tetris.__init__(self, high_score)
            
        if curses.has_colors():
            curses.start_color()
            if curses.can_change_color():
                curses.init_color(curses.COLOR_YELLOW, 1000, 500, 0)
            for mino_type, color in self.MINO_COLOR.items(): 
                curses.init_pair(color, color, curses.COLOR_WHITE)
                if color == curses.COLOR_ORANGE:
                    Window.MINO_COLOR[mino_type] = curses.color_pair(curses.COLOR_YELLOW)
                else:
                    Window.MINO_COLOR[mino_type] = curses.color_pair(color)|curses.A_BOLD
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        scr.timeout(0)
        scr.getch()
        self.scr = scr

        left_x = (curses.COLS-self.WIDTH) // 2
        top_y = (curses.LINES-self.HEIGHT) // 2
        side_width = (self.WIDTH - Matrix.WIDTH) // 2 - 1
        side_height = self.HEIGHT - Hold.HEIGHT
        right_x = left_x + Matrix.WIDTH + side_width + 2
        bottom_y = top_y + Hold.HEIGHT

        self.matrix_window = Matrix(self, left_x, top_y)
        self.hold_window = Hold(self, side_width, left_x, top_y)
        self.next_window = Next(self, side_width, right_x, top_y)
        self.stats_window = Stats(self, side_width, side_height, left_x, bottom_y)
        self.controls_window = ControlsWindow(self, side_width, side_height, right_x, bottom_y)

        self.actions = {
            self.controls_window["QUIT"]: self.quit,
            self.controls_window["PAUSE"]: self.pause,
            self.controls_window["HOLD"]: self.hold_piece,
            self.controls_window["MOVE LEFT"]: self.move_left,
            self.controls_window["MOVE RIGHT"]: self.move_right,
            self.controls_window["SOFT DROP"]: self.soft_drop,
            self.controls_window["ROTATE COUNTER"]: self.rotate_counterclockwise,
            self.controls_window["ROTATE CLOCKWISE"]: self.rotate_clockwise,
            self.controls_window["HARD DROP"]: self.hard_drop
        }

        
        self.paused = False
        
        for arg in sys.argv[1:]:
            if arg.startswith("--level="):
                try:
                    level = int(arg[8:])
                except ValueError:
                    sys.exit(HELP_MSG)
                else:
                    level = max(1, level)
                    level = min(15, level)
                    break
        else:
            level = 1
        self.new_game(level)
        
        self.matrix_window.refresh()
        self.hold_window.refresh()
        self.next_window.refresh()
        self.stats_window.refresh()
        
        scheduler.repeat("time", 1, self.stats_window.refresh_time)
        scheduler.repeat("input", self.AUTOSHIFT_DELAY, self.process_input)

        try:
            scheduler.run()
        except KeyboardInterrupt:
            self.quit()

    def new_piece(self):
        Tetris.new_piece(self)
        self.next_window.refresh()
        self.matrix_window.refresh()

    def process_input(self):
        try:
            action = self.actions[self.scr.getkey()]
        except (curses.error, KeyError):
            pass
        else:
            action()
            self.matrix_window.refresh()

    def pause(self):
        Tetris.pause(self)
        self.paused = True
        self.hold_window.refresh(paused=True)
        self.matrix_window.refresh(paused=True)
        self.next_window.refresh(paused=True)
        self.scr.timeout(-1)
        
        while True:
            key = self.scr.getkey()
            if key == self.controls_window["QUIT"]:
                self.quit()
                break
            elif key == self.controls_window["PAUSE"]:
                self.scr.timeout(0)
                self.hold_window.refresh()
                self.matrix_window.refresh()
                self.next_window.refresh()
                self.stats_window.time = time.time() - self.stats_window.time
                break

    def hold_piece(self):
        Tetris.hold_piece(self)
        self.hold_window.refresh()

    def game_over(self):
        Tetris.game_over(self)
        self.time = time.time() - self.time
        self.matrix_window.refresh()
        if curses.has_colors():
            for color in self.MINO_COLOR.values():
                curses.init_pair(color, color, curses.COLOR_BLACK)
        for y, word in enumerate((("GA", "ME") ,("OV", "ER")), start=Matrix.NB_LINES//2):
            for x, syllable in enumerate(word, start=Matrix.NB_COLS//2-1):
                color = self.matrix[y][x]
                if color is None:
                    color = curses.COLOR_BLACK
                else:
                    color |= curses.A_REVERSE
                self.matrix_window.window.addstr(y, x*2+1, syllable, color)
        self.matrix_window.window.refresh()
        curses.beep()
        self.scr.timeout(-1)
        while self.scr.getkey() != self.controls_window["QUIT"]:
            pass
        self.time = time.time() - self.time
        self.quit()

    def quit(self):
        self.stats_window.save()
        t = time.localtime(time.time() - self.time)
        sys.exit(
            "SCORE\t{:n}\n".format(self.score) +
            "HIGH\t{:n}\n".format(self.high_score) +
            "TIME\t%02d:%02d:%02d\n" % (t.tm_hour-1, t.tm_min, t.tm_sec) +
            "LEVEL\t%d\n" % self.level
        )


def main():
    if "--help" in sys.argv[1:] or "/?" in sys.argv[1:]:
        print(HELP_MSG)
    else:
        if "--reset" in sys.argv[1:]:
            controls = ControlsParser()
            controls.reset()
            controls.edit()
        elif "--edit" in sys.argv[1:]:
            ControlsParser().edit()
            
        locale.setlocale(locale.LC_ALL, '')
        if locale.getpreferredencoding() == 'UTF-8':
            os.environ["NCURSES_NO_UTF8_ACS"] = "1"
        curses.wrapper(Game)


if __name__ == "__main__":
    main()
