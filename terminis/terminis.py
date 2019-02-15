# -*- coding: utf-8 -*-

import sys
try:
    import curses
except ImportError:
    sys.exit(
"""This program requires curses.
You can install it on Windows with:
pip install --user windows-curses
"""
    )
import random
import sched
import time
import os
import locale
import subprocess
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


DIR_NAME = "Terminis"

HELP_MSG = """terminis [--edit|--help|n]

Tetris clone for terminal

  --edit: edit controls in text editor
  --help: show command usage (this message)
  n (integer between 1 and 15): start at level n
"""


locale.setlocale(locale.LC_ALL, '')
if locale.getpreferredencoding() == 'UTF-8':
    os.environ["NCURSES_NO_UTF8_ACS"] = "1"

scheduler = sched.scheduler(time.time, lambda delay: curses.napms(int(delay*1000)))


class Rotation:
    CLOCKWISE = 1
    COUNTERCLOCKWISE = -1


class Color:
    BLACK = 0
    WHITE = 1
    YELLOW = 2
    RED = 3
    GREEN = 4
    BLUE = 5
    MAGENTA = 6
    CYAN = 7
    ORANGE = 8


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x+other.x, self.y+other.y)


class Movement:
    LEFT = Point(-1, 0)
    RIGHT = Point(1, 0)
    DOWN = Point(0, 1)
    STILL = Point(0, 0)


class Mino:
    def __init__(self, position, color):
        self.position = position
        self.color = color


class Tetromino:
    SUPER_ROTATION_SYSTEM = (
        {
            Rotation.COUNTERCLOCKWISE: (Point(0, 0), Point(1, 0), Point(1, -1), Point(0, 2), Point(1, 2)),
            Rotation.CLOCKWISE: (Point(0, 0), Point(-1, 0), Point(-1, -1), Point(0, 2), Point(-1, 2)),
        },
        {
            Rotation.COUNTERCLOCKWISE: (Point(0, 0), Point(1, 0), Point(1, 1), Point(0, -2), Point(1, -2)),
            Rotation.CLOCKWISE: (Point(0, 0), Point(1, 0), Point(1, 1), Point(0, -2), Point(1, -2)),
        },
        {
            Rotation.COUNTERCLOCKWISE: (Point(0, 0), Point(-1, 0), Point(-1, -1), Point(0, 2), Point(-1, 2)),
            Rotation.CLOCKWISE: (Point(0, 0), Point(1, 0), Point(1, -1), Point(0, 2), Point(1, 2)),
        },
        {
            Rotation.COUNTERCLOCKWISE: (Point(0, 0), Point(-1, 0), Point(-1, 1), Point(0, -2), Point(-1, -2)),
            Rotation.CLOCKWISE: (Point(0, 0), Point(-1, 0), Point(-1, 1), Point(0, 2), Point(-1, -2))
        }
    )
    lock_delay = 0.5
    fall_delay = 1

    def __init__(self, matrix, position):
        self.matrix = matrix
        self.position = position
        self.minoes = tuple(
            Mino(position, self.COLOR)
            for position in self.MINOES_POSITIONS
        )
        self.orientation = 0
        self.rotation_point_5_used = False
        self.rotated_last = False
        self.lock_timer = None
        self.fall_timer = None
        self.hold_enabled = True

    def move(self, movement, lock=True):
        potential_position = self.position + movement
        if all(
            self.matrix.is_free_cell(mino.position+potential_position)
            for mino in self.minoes
        ):
            self.position = potential_position
            self.postpone_lock()
            self.rotated_last = False
            self.matrix.refresh()
            return True
        else:
            if lock and movement == Movement.DOWN:
                self.locking()
            return False

    def soft_drop(self):
        if self.move(Movement.DOWN):
            self.matrix.game.stats.piece_dropped(1)

    def hard_drop(self):
        if self.lock_timer:
            scheduler.cancel(self.lock_timer)
            self.lock_timer = None
        lines = 0
        while self.move(Movement.DOWN, lock=False):
            lines += 2
        self.matrix.game.stats.piece_dropped(lines)
        self.lock()

    def rotate(self, direction):
        potential_minoes_positions = tuple(
            Point(-direction*mino.position.y, direction*mino.position.x)
            for mino in self.minoes
        )
        for rotation_point, liberty_degree in enumerate(self.SUPER_ROTATION_SYSTEM[self.orientation][direction], start=1):
            potential_position = self.position + liberty_degree
            if all(
                self.matrix.is_free_cell(potential_mino_position+potential_position)
                for potential_mino_position in potential_minoes_positions
            ):
                self.orientation = (self.orientation+direction) % 4
                self.position = potential_position
                for mino, potential_mino_position in zip(self.minoes, potential_minoes_positions):
                    mino.position = potential_mino_position
                self.postpone_lock()
                self.rotated_last = True
                if rotation_point == 5:
                    self.rotation_point_5_used = True
                self.matrix.refresh()
                return True
        else:
            return False

    def fall(self):
        self.fall_timer = scheduler.enter(self.fall_delay, 2, self.fall, tuple())
        self.move(Movement.DOWN)

    def locking(self):
        if not self.lock_timer:
            self.lock_timer = scheduler.enter(self.lock_delay, 1, self.lock, tuple())
            self.matrix.refresh()

    def postpone_lock(self):
        if self.lock_timer:
            scheduler.cancel(self.lock_timer)
            self.lock_timer = scheduler.enter(self.lock_delay, 1, self.lock, tuple())

    def lock(self):
        self.lock_timer = None
        if not self.move(Movement.DOWN, lock=False):
            if self.fall_timer:
                scheduler.cancel(self.fall_timer)
                self.fall_timer = None
            if all(self.position.y + mino.position.y <= 0 for mino in self.minoes):
                self.matrix.game.over()
            else:
                self.matrix.lock(self.t_spin())

    def t_spin(self):
        return ""


class O(Tetromino):
    MINOES_POSITIONS = (Point(0, 0), Point(1, 0), Point(0, -1), Point(1, -1))
    COLOR = Color.YELLOW

    def rotate(self, direction):
        return False

class I(Tetromino):
    SUPER_ROTATION_SYSTEM = (
        {
            Rotation.COUNTERCLOCKWISE: (Point(0, 1), Point(-1, 1), Point(2, 1), Point(-1, -1), Point(2, 2)),
            Rotation.CLOCKWISE: (Point(1, 0), Point(-1, 0), Point(2, 0), Point(-1, 1), Point(2, -2)),
        },
        {
            Rotation.COUNTERCLOCKWISE: (Point(-1, 0), Point(1, 0), Point(-2, 0), Point(1, -1), Point(-2, 2)),
            Rotation.CLOCKWISE: (Point(0, 1), Point(-1, 1), Point(2, 1), Point(-1, -1), Point(2, 2)),
        },
        {
            Rotation.COUNTERCLOCKWISE: (Point(0, -1), Point(1, -1), Point(-2, -1), Point(1, 1), Point(-2, -2)),
            Rotation.CLOCKWISE: (Point(-1, 0), Point(1, 0), Point(-2, 0), Point(1, -1), Point(-2, 2)),
        },
        {
            Rotation.COUNTERCLOCKWISE: (Point(1, 0), Point(-1, 0), Point(2, 0), Point(-1, 1), Point(2, -2)),
            Rotation.CLOCKWISE: (Point(0, 1), Point(1, -1), Point(-2, -1), Point(1, 1), Point(-2, -2)),
        },
    )
    MINOES_POSITIONS = (Point(-1, 0), Point(0, 0), Point(1, 0), Point(2, 0))
    COLOR = Color.CYAN

class T(Tetromino):
    MINOES_POSITIONS = (Point(-1, 0), Point(0, 0), Point(0, -1), Point(1, 0))
    COLOR = Color.MAGENTA
    T_SLOT = (Point(-1, -1), Point(1, -1), Point(1, 1), Point(-1, 1))

    def t_spin(self):
        if self.rotated_last:
            a = not self.matrix.is_free_cell(self.position + self.T_SLOT[self.orientation])
            b = not self.matrix.is_free_cell(self.position + self.T_SLOT[(1+self.orientation)%4])
            c = not self.matrix.is_free_cell(self.position + self.T_SLOT[(3+self.orientation)%4])
            d = not self.matrix.is_free_cell(self.position + self.T_SLOT[(2+self.orientation)%4])
            if self.rotation_point_5_used or (a and b and (c or d)):
                return "T-SPIN"
            elif c and d and (a or b):
                return "MINI T-SPIN"
        return ""

class L(Tetromino):
    MINOES_POSITIONS = (Point(-1, 0), Point(0, 0), Point(1, 0), Point(1, -1))
    COLOR = Color.ORANGE

class J(Tetromino):
    MINOES_POSITIONS = (Point(-1, -1), Point(-1, 0), Point(0, 0), Point(1, 0))
    COLOR = Color.BLUE

class S(Tetromino):
    MINOES_POSITIONS = (Point(-1, 0), Point(0, 0), Point(0, -1), Point(1, -1))
    COLOR = Color.GREEN

class Z(Tetromino):
    MINOES_POSITIONS = (Point(-1, -1), Point(0, -1), Point(0, 0), Point(1, 0))
    COLOR = Color.RED


class Window:
    def __init__(self, width, height, begin_x, begin_y):
        self.window = curses.newwin(height, width, begin_y, begin_x)
        self.has_colors = curses.has_colors()
        if self.TITLE:
            self.title_begin_x = (width-len(self.TITLE)) // 2 + 1
        self.piece = None
        self.refresh()

    def draw_border(self):
        self.window.erase()
        self.window.border()
        if self.TITLE:
            self.window.addstr(0, self.title_begin_x, self.TITLE, curses.A_BOLD)

    def draw_piece(self):
        if self.piece:
            color = Color.WHITE|curses.A_BLINK if self.piece.lock_timer else self.piece.COLOR
            for mino in self.piece.minoes:
                position = mino.position + self.piece.position
                self.draw_mino(position.x, position.y, color)

    def draw_mino(self, x, y, color):
        if y >= 0:
            if self.has_colors:
                self.window.addstr(y, x*2+1, "██", curses.color_pair(color))
            else:
                self.window.addstr(y, x*2+1, "██")


class Matrix(Window):
    NB_COLS = 10
    NB_LINES = 21
    WIDTH = NB_COLS*2+2
    HEIGHT = NB_LINES+1
    PIECE_POSITION = Point(4, 0)
    TITLE = ""

    def __init__(self, game, begin_x, begin_y):
        begin_x += (game.WIDTH - self.WIDTH) // 2
        begin_y += (game.HEIGHT - self.HEIGHT) // 2
        self.game = game
        self.cells = [
            [None for x in range(self.NB_COLS)]
            for y in range(self.NB_LINES)
        ]
        Window.__init__(self, self.WIDTH, self.HEIGHT, begin_x, begin_y)

    def refresh(self, paused=False):
        self.draw_border()
        if paused:
            self.window.addstr(11, 9, "PAUSE", curses.A_BOLD)
        else:
            for y, line in enumerate(self.cells):
                for x, color in enumerate(line):
                    if color:
                        self.draw_mino(x, y, color)
            self.draw_piece()
        self.window.refresh()

    def is_free_cell(self, position):
        return (
            0 <= position.x < self.NB_COLS
            and position.y < self.NB_LINES
            and not (position.y >= 0 and self.cells[position.y][position.x])
        )

    def lock(self, t_spin):
        for mino in self.piece.minoes:
            position = mino.position + self.piece.position
            if position.y >= 0:
                self.cells[position.y][position.x] = mino.color
        nb_lines_cleared = 0
        for y, line in enumerate(self.cells):
            if all(mino for mino in line):
                self.cells.pop(y)
                self.cells.insert(0, [None for x in range(self.NB_COLS)])
                nb_lines_cleared += 1
        self.game.stats.piece_locked(nb_lines_cleared, t_spin)
        self.game.new_piece()


class HoldNext(Window):
    HEIGHT = 6
    PIECE_POSITION = Point(6, 3)

    def __init__(self, width, begin_x, begin_y):
        Window.__init__(self, width, self.HEIGHT, begin_x, begin_y)

    def refresh(self, paused=False):
        self.draw_border()
        if not paused:
            self.draw_piece()
        self.window.refresh()


class Hold(HoldNext):
    TITLE = "HOLD"


class Next(HoldNext):
    TITLE = "NEXT"


class Stats(Window):
    SCORES = (
        {"": 0, "MINI T-SPIN": 1, "T-SPIN": 4},
        {"": 1, "MINI T-SPIN": 2, "T-SPIN": 8},
        {"": 3, "T-SPIN": 12},
        {"": 5, "T-SPIN": 16},
        {"": 8}
    )
    LINES_CLEARED_NAMES = ("", "SINGLE", "DOUBLE", "TRIPLE", "TETRIS")
    TITLE = "STATS"
    FILE_NAME = ".high_score"
    if sys.platform == "win32":
        DIR_PATH = os.environ.get("appdata", os.path.expanduser("~\Appdata\Roaming"))
    else:
        DIR_PATH = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    DIR_PATH = os.path.join(DIR_PATH, DIR_NAME)
    FILE_PATH = os.path.join(DIR_PATH, FILE_NAME)

    def __init__(self, game, width, height, begin_x, begin_y):
        if len(sys.argv) >= 2:
            try:
                self.level = int(sys.argv[1])
            except ValueError:
                sys.exit(HELP_MSG)
            else:
                self.level = max(1, self.level)
                self.level = min(15, self.level)
                self.level -= 1
        else:
            self.level = 0

        self.game = game
        self.width = width
        self.height = height
        self.goal = 0
        self.score = 0
        try:
            with open(self.FILE_PATH, "r") as f:
               self.high_score = int(f.read())
        except:
            self.high_score = 0
        self.combo = -1
        self.time = time.time()
        self.lines_cleared = 0
        self.clock_timer = None
        self.strings = []
        Window.__init__(self, width, height, begin_x, begin_y)
        self.new_level()

    def refresh(self):
        self.draw_border()
        self.window.addstr(2, 2, "SCORE\t{:n}".format(self.score))
        if self.score >= self.high_score:
            self.window.addstr(3, 2, "HIGH\t{:n}".format(self.high_score), curses.A_BLINK|curses.A_BOLD)
        else:
            self.window.addstr(3, 2, "HIGH\t{:n}".format(self.high_score))
        t = time.localtime(time.time() - self.time)
        self.window.addstr(4, 2, "TIME\t%02d:%02d:%02d" % (t.tm_hour-1, t.tm_min, t.tm_sec))
        self.window.addstr(5, 2, "LEVEL\t%d" % self.level)
        self.window.addstr(6, 2, "GOAL\t%d" % self.goal)
        self.window.addstr(7, 2, "LINES\t%d" % self.lines_cleared)
        start_y = self.height - len(self.strings) - 2
        for y, string in enumerate(self.strings, start=start_y):
            x = (self.width-len(string)) // 2 + 1
            self.window.addstr(y, x, string)
        self.window.refresh()

    def clock(self):
        self.clock_timer = scheduler.enter(1, 3, self.clock, tuple())
        self.refresh()

    def new_level(self):
        self.level += 1
        Tetromino.fall_delay = pow(0.8 - ((self.level-1)*0.007), self.level-1)
        if self.level > 15:
            Tetromino.lock_delay = 0.5 * pow(0.9, self.level-15)
        self.goal += 5 * self.level
        self.refresh()

    def piece_dropped(self, lines):
        self.score += lines
        if self.score > self.high_score:
            self.high_score = self.score
        self.refresh()

    def piece_locked(self, nb_lines, t_spin):
        self.strings = []
        if t_spin:
            self.strings.append(t_spin)
        if nb_lines:
            self.strings.append(self.LINES_CLEARED_NAMES[nb_lines])
            self.combo += 1
        else:
            self.combo = -1
        if nb_lines or t_spin:
            self.lines_cleared += nb_lines
            ds = self.SCORES[nb_lines][t_spin]
            self.goal -= ds
            ds *= 100 * self.level
            self.score += ds
            self.strings.append(str(ds))
        if self.combo >= 1:
            self.strings.append("COMBO x%d" % self.combo)
            ds = (20 if nb_lines==1 else 50) * self.combo * self.level
            self.score += ds
            self.strings.append(str(ds))
        if nb_lines == 4 or (nb_lines and t_spin):
            curses.beep()
        if self.score > self.high_score:
            self.high_score = self.score
        if self.goal <= 0:
            self.new_level()
        else:
            self.refresh()

    def save(self):
        if not os.path.exists(self.DIR_PATH):
            os.mkdir(self.DIR_PATH)
        try:
            with open(self.FILE_PATH, mode='w') as f:
                f.write(str(self.high_score))
        except Exception as e:
            print("High score could not be saved:")
            print(e)


class Controls(Window, configparser.SafeConfigParser):
    TITLE = "CONTROLS"
    FILE_NAME = "config.cfg"
    if sys.platform == "win32":
        DIR_PATH = os.environ.get("appdata", os.path.expanduser("~\Appdata\Roaming"))
    else:
        DIR_PATH = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    DIR_PATH = os.path.join(DIR_PATH, DIR_NAME)
    FILE_PATH = os.path.join(DIR_PATH, FILE_NAME)
    SECTION = "CONTROLS"

    def __init__(self, width, height, begin_x, begin_y):
        configparser.SafeConfigParser.__init__(self)
        self.optionxform = str
        self.add_section(self.SECTION)
        self["MOVE LEFT"] = "KEY_LEFT"
        self["MOVE RIGHT"] = "KEY_RIGHT"
        self["SOFT DROP"] = "KEY_DOWN"
        self["HARD DROP"] = "SPACE"
        self["ROTATE COUNTER"] = "KEY_UP"
        self["ROTATE CLOCKWISE"] = "ENTER"
        self["HOLD"] = "h"
        self["PAUSE"] = "p"
        self["QUIT"] = "q"
        if os.path.exists(self.FILE_PATH):
            self.read(self.FILE_PATH)
        else:
            if not os.path.exists(self.DIR_PATH):
                os.mkdir(self.DIR_PATH)
            try:
                with open(self.FILE_PATH, 'w') as f:
                    f.write(
"""# You can change key below.
# Acceptable values are:
# * `SPACE`, `TAB`, `ENTER`
# * printable characters (`q`, `*`...)
# * curses's constants name starting with `KEY_`
#   See https://docs.python.org/3/library/curses.html?highlight=curses#constants

"""
                    )
                    self.write(f)
            except Exception as e:
                print("Configuration could not be saved:")
                print(e)
        Window.__init__(self, width, height, begin_x, begin_y)
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

    def __getitem__(self, key):
        return self.get(self.SECTION, key)
    
    def __setitem__(self, key, value):
        self.set(self.SECTION, key, value)


class Game:
    WIDTH = 80
    HEIGHT = Matrix.HEIGHT
    AUTOREPEAT_DELAY = 0.02

    def __init__(self, scr):
        self.scr = scr

        if curses.has_colors():
            curses.use_default_colors()
            curses.start_color()
            if curses.COLORS >= 16:
                if curses.can_change_color():
                    curses.init_color(curses.COLOR_YELLOW, 1000, 500, 0)
                curses.init_pair(Color.ORANGE, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
                curses.init_pair(Color.RED, curses.COLOR_RED+8, curses.COLOR_RED+8)
                curses.init_pair(Color.GREEN, curses.COLOR_GREEN+8, curses.COLOR_GREEN+8)
                curses.init_pair(Color.YELLOW, curses.COLOR_YELLOW+8, curses.COLOR_YELLOW+8)
                curses.init_pair(Color.BLUE, curses.COLOR_BLUE+8, curses.COLOR_BLUE+8)
                curses.init_pair(Color.MAGENTA, curses.COLOR_MAGENTA+8, curses.COLOR_MAGENTA+8)
                curses.init_pair(Color.CYAN, curses.COLOR_CYAN+8, curses.COLOR_CYAN+8)
                curses.init_pair(Color.WHITE, curses.COLOR_WHITE+8, curses.COLOR_WHITE+8)
            else:
                curses.init_pair(Color.ORANGE, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
                curses.init_pair(Color.RED, curses.COLOR_RED, curses.COLOR_RED)
                curses.init_pair(Color.GREEN, curses.COLOR_GREEN, curses.COLOR_GREEN)
                curses.init_pair(Color.YELLOW, curses.COLOR_WHITE, curses.COLOR_WHITE)
                curses.init_pair(Color.BLUE, curses.COLOR_BLUE, curses.COLOR_BLUE)
                curses.init_pair(Color.MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
                curses.init_pair(Color.CYAN, curses.COLOR_CYAN, curses.COLOR_CYAN)
                curses.init_pair(Color.WHITE, curses.COLOR_WHITE, curses.COLOR_WHITE)

        try:
            curses.curs_set(0)
        except curses.error:
            pass

        self.scr.timeout(0)
        self.scr.getch()

        left_x = (curses.COLS-self.WIDTH) // 2
        top_y = (curses.LINES-self.HEIGHT) // 2
        side_width = (self.WIDTH - Matrix.WIDTH) // 2
        side_height = self.HEIGHT - Hold.HEIGHT
        right_x = left_x + Matrix.WIDTH + side_width
        bottom_y = top_y + Hold.HEIGHT

        self.matrix = Matrix(self, left_x, top_y)
        self.hold = Hold(side_width, left_x, top_y)
        self.next = Next(side_width, right_x, top_y)
        self.stats = Stats(self, side_width, side_height, left_x, bottom_y)
        self.controls = Controls(side_width, side_height, right_x, bottom_y)

        self.actions = {
            self.controls["QUIT"]: self.quit,
            self.controls["PAUSE"]: self.pause,
            self.controls["HOLD"]: self.swap,
            self.controls["MOVE LEFT"]: lambda: self.matrix.piece.move(Movement.LEFT),
            self.controls["MOVE RIGHT"]: lambda: self.matrix.piece.move(Movement.RIGHT),
            self.controls["SOFT DROP"]: lambda: self.matrix.piece.soft_drop(),
            self.controls["ROTATE COUNTER"]: lambda: self.matrix.piece.rotate(Rotation.COUNTERCLOCKWISE),
            self.controls["ROTATE CLOCKWISE"]: lambda: self.matrix.piece.rotate(Rotation.CLOCKWISE),
            self.controls["HARD DROP"]: lambda: self.matrix.piece.hard_drop()
        }

        self.playing = True
        self.paused = False
        self.stats.time = time.time()
        self.stats.clock_timer = scheduler.enter(1, 3, self.stats.clock, tuple())
        self.random_bag = []
        self.next.piece = self.random_piece()(self.matrix, Next.PIECE_POSITION)
        self.new_piece()
        self.input_timer = scheduler.enter(self.AUTOREPEAT_DELAY, 2, self.process_input, tuple())

        try:
            scheduler.run()
        except KeyboardInterrupt:
            self.quit()

    def random_piece(self):
        if not self.random_bag:
            self.random_bag = [O, I, T, L, J, S, Z]
            random.shuffle(self.random_bag)
        return self.random_bag.pop()

    def new_piece(self, held_piece=None):
        if not held_piece:
            self.matrix.piece = self.next.piece
            self.next.piece = self.random_piece()(self.matrix, Next.PIECE_POSITION)
            self.next.refresh()
        self.matrix.piece.position = Matrix.PIECE_POSITION
        if self.matrix.piece.move(Movement.STILL, lock=False):
            self.matrix.piece.fall_timer = scheduler.enter(Tetromino.fall_delay, 2, self.matrix.piece.fall, tuple())
        else:
            self.over()

    def process_input(self):
        self.input_timer = scheduler.enter(self.AUTOREPEAT_DELAY, 2, self.process_input, tuple())
        try:
            action = self.actions[self.scr.getkey()]
        except (curses.error, KeyError):
            pass
        else:
            action()

    def pause(self):
        self.stats.time = time.time() - self.stats.time
        self.paused = True
        self.hold.refresh(paused=True)
        self.matrix.refresh(paused=True)
        self.next.refresh(paused=True)
        self.scr.timeout(-1)
        while True:
            key = self.scr.getkey()
            if key == self.controls["QUIT"]:
                self.quit()
                break
            elif key == self.controls["PAUSE"]:
                self.scr.timeout(0)
                self.hold.refresh()
                self.matrix.refresh()
                self.next.refresh()
                self.stats.time = time.time() - self.stats.time
                break

    def swap(self):
        if self.matrix.piece.hold_enabled:
            if self.matrix.piece.fall_timer:
                scheduler.cancel(self.matrix.piece.fall_timer)
                self.matrix.piece.fall_timer = None
            if self.matrix.piece.lock_timer:
                scheduler.cancel(self.matrix.piece.lock_timer)
                self.matrix.piece.lock_timer = None
            self.matrix.piece, self.hold.piece = self.hold.piece, self.matrix.piece
            self.hold.piece.position = self.hold.PIECE_POSITION
            for mino, position in zip(self.hold.piece.minoes, self.hold.piece.MINOES_POSITIONS):
                mino.position = position
            self.hold.piece.hold_enabled = False
            self.hold.refresh()
            self.new_piece(self.matrix.piece)

    def over(self):
        self.matrix.refresh()
        self.matrix.window.addstr(10, 9, "GAME", curses.A_BOLD)
        self.matrix.window.addstr(11, 9, "OVER", curses.A_BOLD)
        self.matrix.window.refresh()
        self.scr.timeout(-1)
        while self.scr.getkey() != self.controls["QUIT"]:
            pass
        self.quit()

    def quit(self):
        self.playing = False
        if self.matrix.piece.fall_timer:
            scheduler.cancel(self.matrix.piece.fall_timer)
            self.matrix.piece.fall_timer = None
        if self.matrix.piece.lock_timer:
            scheduler.cancel(self.matrix.piece.lock_timer)
            self.matrix.piece.lock_timer = None
        if self.stats.clock_timer:
            scheduler.cancel(self.stats.clock_timer)
            self.stats.clock_timer = None
        if self.input_timer:
            scheduler.cancel(self.input_timer)
            self.input_timer = None
        self.stats.save()


def main():
    if "--edit" in sys.argv[1:]:
        edit()
    elif "--help" in sys.argv[1:] or "/?" in sys.argv[1:]:
        print(HELP_MSG)
    else:
        curses.wrapper(Game)
        
def edit():
    if sys.platform == "win32":
        try:
            subprocess.call(["edit.com", Controls.FILE_PATH])
        except FileNotFoundError:
            subprocess.call(["notepad.exe", Controls.FILE_PATH])
    else:
        subprocess.call(["${EDITOR:-vi}", Controls.FILE_PATH])
    


if __name__ == "__main__":
    main()
