# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import psutil

try:
    import curses
except ImportError:
    sys.exit(
"""This program requires curses.
You can install it on Windows with:
pip install --user windows-curses"""
    )
else:
    curses.COLOR_ORANGE = curses.COLOR_WHITE
    
import random
import sched
import time
import os
import locale
import subprocess

try:
    from configparser import ConfigParser
except ImportError: # Python2
    from ConfigParser import SafeConfigParser as ConfigParser


DIR_NAME = "Terminis"
HELP_MSG = """terminis [options]

Tetris clone for terminal

  --help\t-h\tshow command usage (this message)
  --edit\t-e\tedit controls in text editor
  --reset\t-r\treset to default controls settings
  --level=n\t\tstart at level n (integer between 1 and 15)"""


class Rotation:
    CLOCKWISE = 1
    COUNTERCLOCKWISE = -1


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x+other.x, self.y+other.y)


class Movement:
    LEFT  = Point(-1, 0)
    RIGHT = Point(1, 0)
    DOWN  = Point(0, 1)


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
            sched.scheduler.cancel(self, self.pop(name))

scheduler = Scheduler()


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
    color_pair = curses.COLOR_BLACK

    def __init__(self, matrix, position):
        self.matrix = matrix
        self.position = position
        self.minoes_positions = self.MINOES_POSITIONS
        self.orientation = 0
        self.rotation_point_5_used = False
        self.rotated_last = False
        self.hold_enabled = True
        
    def move_rotate(self, movement, minoes_positions):
        potential_position = self.position + movement
        if all(
            self.matrix.is_free_cell(potential_position+mino_position)
            for mino_position in minoes_positions
        ):
            self.position = potential_position
            if "lock" in scheduler:
                scheduler.cancel("lock")
                scheduler.single_shot("lock", self.lock_delay, self.matrix.lock)
            return True
        else:
            return False
        
    def move(self, movement, lock=True, refresh=True):
        if self.move_rotate(movement, self.minoes_positions):
            self.rotated_last = False
            if refresh:
                self.matrix.refresh()
            return True
        else:
            if (
                lock
                and movement == Movement.DOWN
                and "lock" not in scheduler
            ):
                scheduler.single_shot("lock", self.lock_delay, self.matrix.lock)
                self.matrix.refresh()
            return False

    def rotate(self, direction):
        rotated_minoes_positions = tuple(
            Point(-direction*mino_position.y, direction*mino_position.x)
            for mino_position in self.minoes_positions
        )
        for rotation_point, liberty_degree in enumerate(self.SUPER_ROTATION_SYSTEM[self.orientation][direction], start=1):
            if self.move_rotate(liberty_degree, rotated_minoes_positions):
                self.minoes_positions = rotated_minoes_positions
                self.orientation = (self.orientation+direction) % 4
                self.rotated_last = False
                if rotation_point == 5:
                    self.rotation_point_5_used = True
                self.matrix.refresh()
                return True
        else:
            return False

    def soft_drop(self):
        if self.move(Movement.DOWN):
            self.matrix.game.stats.piece_dropped(1)

    def hard_drop(self):
        lines = 0
        while self.move(Movement.DOWN, lock=False, refresh=False):
            lines += 2
        self.matrix.refresh()
        self.matrix.game.stats.piece_dropped(lines)
        self.matrix.lock()
        
    def fall(self):
        self.move(Movement.DOWN)

    def t_spin(self):
        return ""


class O(Tetromino):
    SUPER_ROTATION_SYSTEM = tuple()
    MINOES_POSITIONS = (Point(0, 0), Point(1, 0), Point(0, -1), Point(1, -1))
    COLOR = curses.COLOR_YELLOW

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
    COLOR = curses.COLOR_CYAN

class T(Tetromino):
    MINOES_POSITIONS = (Point(-1, 0), Point(0, 0), Point(0, -1), Point(1, 0))
    COLOR = curses.COLOR_MAGENTA
    T_SLOT = (Point(-1, -1), Point(1, -1), Point(1, 1), Point(-1, 1))

    def t_spin(self):
        if self.rotated_last:
            a = not self.matrix.is_free_cell(self.position+self.T_SLOT[self.orientation])
            b = not self.matrix.is_free_cell(self.position+self.T_SLOT[(1+self.orientation)%4])
            c = not self.matrix.is_free_cell(self.position+self.T_SLOT[(3+self.orientation)%4])
            d = not self.matrix.is_free_cell(self.position+self.T_SLOT[(2+self.orientation)%4])
            
            if self.rotation_point_5_used or (a and b and (c or d)):
                return "T-SPIN"
            elif c and d and (a or b):
                return "MINI T-SPIN"
        return ""

class L(Tetromino):
    MINOES_POSITIONS = (Point(-1, 0), Point(0, 0), Point(1, 0), Point(1, -1))
    COLOR = curses.COLOR_ORANGE

class J(Tetromino):
    MINOES_POSITIONS = (Point(-1, -1), Point(-1, 0), Point(0, 0), Point(1, 0))
    COLOR = curses.COLOR_BLUE

class S(Tetromino):
    MINOES_POSITIONS = (Point(-1, 0), Point(0, 0), Point(0, -1), Point(1, -1))
    COLOR = curses.COLOR_GREEN

class Z(Tetromino):
    MINOES_POSITIONS = (Point(-1, -1), Point(0, -1), Point(0, 0), Point(1, 0))
    COLOR = curses.COLOR_RED


class Window:
    def __init__(self, width, height, begin_x, begin_y):
        self.window = curses.newwin(height, width, begin_y, begin_x)
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
            if "lock" in scheduler:
                attr = self.piece.color_pair | curses.A_BLINK | curses.A_REVERSE
            else:
                attr = self.piece.color_pair
            for mino_position in self.piece.minoes_positions:
                position = mino_position + self.piece.position
                self.draw_mino(position.x, position.y, attr)

    def draw_mino(self, x, y, attr):
        if y >= 0:
            self.window.addstr(y, x*2+1, "██", attr)


class Matrix(Window):
    NB_COLS = 10
    NB_LINES = 21
    WIDTH = NB_COLS*2+2
    HEIGHT = NB_LINES+1
    PIECE_POSITION = Point(4, -1)
    TITLE = ""

    def __init__(self, game, begin_x, begin_y):
        begin_x += (game.WIDTH - self.WIDTH) // 2
        begin_y += (game.HEIGHT - self.HEIGHT) // 2
        self.game = game
        self.cells = [
            [None for x in range(self.NB_COLS)]
            for y in range(self.NB_LINES)
        ]
        self.piece = None
        Window.__init__(self, self.WIDTH, self.HEIGHT, begin_x, begin_y)

    def refresh(self, paused=False):
        self.draw_border()
        if paused:
            self.window.addstr(11, 9, "PAUSE", curses.A_BOLD)
        else:
            for y, line in enumerate(self.cells):
                for x, color in enumerate(line):
                    if color is not None:
                        self.draw_mino(x, y, color)
            self.draw_piece()
        self.window.refresh()

    def is_free_cell(self, position):
        return (
            0 <= position.x < self.NB_COLS
            and position.y < self.NB_LINES
            and not (position.y >= 0 and self.cells[position.y][position.x] is not None)
        )

    def lock(self):
        if not self.piece.move(Movement.DOWN):
            scheduler.cancel("fall")
            
            t_spin = self.piece.t_spin()
            
            for mino_position in self.piece.minoes_positions:
                position = mino_position + self.piece.position
                if position.y >= 0:
                    self.cells[position.y][position.x] = self.piece.color_pair
                else:
                    self.game.over()
                    return
    
            nb_lines_cleared = 0
            for y, line in enumerate(self.cells):
                if all(mino for mino in line):
                    self.cells.pop(y)
                    self.cells.insert(0, [None for x in range(self.NB_COLS)])
                    nb_lines_cleared += 1
                    
            self.game.stats.piece_locked(nb_lines_cleared, t_spin)
            self.piece = None
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
        {"name": "", "": 0, "MINI T-SPIN": 1, "T-SPIN": 4},
        {"name": "SINGLE", "": 1, "MINI T-SPIN": 2, "T-SPIN": 8},
        {"name": "DOUBLE", "": 3, "T-SPIN": 12},
        {"name": "TRIPLE", "": 5, "T-SPIN": 16},
        {"name": "TETRIS", "": 8}
    )
    TITLE = "STATS"
    FILE_NAME = ".high_score"
    if sys.platform == "win32":
        DIR_PATH = os.environ.get("appdata", os.path.expanduser("~\Appdata\Roaming"))
    else:
        DIR_PATH = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    DIR_PATH = os.path.join(DIR_PATH, DIR_NAME)
    FILE_PATH = os.path.join(DIR_PATH, FILE_NAME)

    def __init__(self, game, width, height, begin_x, begin_y):
        for arg in sys.argv[1:]:
            if arg.startswith("--level="):
                try:
                    self.level = int(arg[8:])
                except ValueError:
                    sys.exit(HELP_MSG)
                else:
                    self.level = max(1, self.level)
                    self.level = min(15, self.level)
                    self.level -= 1
                    break
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
        self.window.addstr(5, 2, "LEVEL\t%d" % self.level)
        self.window.addstr(6, 2, "GOAL\t%d" % self.goal)
        self.window.addstr(7, 2, "LINES\t%d" % self.lines_cleared)
        start_y = self.height - len(self.strings) - 2
        for y, string in enumerate(self.strings, start=start_y):
            x = (self.width-len(string)) // 2 + 1
            self.window.addstr(y, x, string)
        self.refresh_time()
        
    def refresh_time(self):
        t = time.localtime(time.time() - self.time)
        self.window.addstr(4, 2, "TIME\t%02d:%02d:%02d" % (t.tm_hour-1, t.tm_min, t.tm_sec))
        self.window.refresh()

    def new_level(self):
        self.level += 1
        if self.level <= 20:
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
            self.strings.append(self.SCORES[nb_lines]["name"])
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
            os.makedirs(self.DIR_PATH)
        try:
            with open(self.FILE_PATH, mode='w') as f:
                f.write(str(self.high_score))
        except Exception as e:
            print("High score could not be saved:")
            print(e)


class ControlsParser(ConfigParser):
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
        ConfigParser.__init__(self)
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

    def __init__(self, width, height, begin_x, begin_y):
        ControlsParser.__init__(self)
        self.read(self.FILE_PATH)
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


class Music:
    PATH = "music.sh"

    def __init__(self):
        self.process = None

    def play(self):
        self.process = subprocess.Popen(["sh", self.PATH])

    def stop(self):
        if self.process:
            for proc in psutil.Process(self.process.pid).children(recursive=True):
                proc.terminate()
            self.process.terminate()
            self.process = None


class Game:
    WIDTH = 80
    HEIGHT = Matrix.HEIGHT
    AUTOREPEAT_DELAY = 0.02
    TETROMINOES = (O, I, T, L, J, S, Z)

    def __init__(self, scr):
        if curses.has_colors():
            curses.start_color()
            if curses.can_change_color():
                curses.init_color(curses.COLOR_YELLOW, 1000, 500, 0)
            for tetromino_class in self.TETROMINOES: 
                curses.init_pair(tetromino_class.COLOR, tetromino_class.COLOR, curses.COLOR_WHITE)
                if tetromino_class.COLOR == curses.COLOR_ORANGE:
                    tetromino_class.color_pair = curses.color_pair(curses.COLOR_YELLOW)
                else:
                    tetromino_class.color_pair = curses.color_pair(tetromino_class.COLOR)|curses.A_BOLD
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

        self.matrix = Matrix(self, left_x, top_y)
        self.hold = Hold(side_width, left_x, top_y)
        self.next = Next(side_width, right_x, top_y)
        self.stats = Stats(self, side_width, side_height, left_x, bottom_y)
        self.controls = ControlsWindow(side_width, side_height, right_x, bottom_y)
        self.music = Music()

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

        self.paused = False
        self.random_bag = []
        self.next.piece = self.random_piece()
        self.new_piece()
        scheduler.repeat("time", 1, self.stats.refresh_time)
        scheduler.repeat("input", self.AUTOREPEAT_DELAY, self.process_input)
        self.music.play()

        try:
            scheduler.run()
        except KeyboardInterrupt:
            self.quit()

    def random_piece(self):
        if not self.random_bag:
            self.random_bag = list(self.TETROMINOES)
            random.shuffle(self.random_bag)
        return self.random_bag.pop()(self.matrix, Next.PIECE_POSITION)

    def new_piece(self):
        scheduler.cancel("lock")
        if not self.matrix.piece:
            self.matrix.piece, self.next.piece = self.next.piece, self.random_piece()
            self.next.refresh()
        self.matrix.piece.position = Matrix.PIECE_POSITION
        if self.matrix.piece.move(Movement.DOWN):
            scheduler.repeat("fall", Tetromino.fall_delay, self.matrix.piece.fall)
            self.matrix.refresh()
        else:
            self.over()

    def process_input(self):
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
        self.music.stop()
        
        while True:
            key = self.scr.getkey()
            if key == self.controls["QUIT"]:
                self.quit()
                break
            elif key == self.controls["PAUSE"]:
                break

        self.scr.timeout(0)
        self.hold.refresh()
        self.matrix.refresh()
        self.next.refresh()
        self.stats.time = time.time() - self.stats.time
        self.music.play()

    def swap(self):
        if self.matrix.piece.hold_enabled:
            scheduler.cancel("fall")
            scheduler.cancel("lock")
            self.matrix.piece, self.hold.piece = self.hold.piece, self.matrix.piece
            self.hold.piece.position = self.hold.PIECE_POSITION
            self.hold.piece.minoes_positions = self.hold.piece.MINOES_POSITIONS
            self.hold.piece.hold_enabled = False
            self.hold.refresh()
            self.new_piece()

    def over(self):
        self.stats.time = time.time() - self.stats.time
        self.matrix.refresh()
        if curses.has_colors():
            for tetromino_class in self.TETROMINOES: 
                curses.init_pair(tetromino_class.COLOR, tetromino_class.COLOR, curses.COLOR_BLACK)
        for y, word in enumerate((("GA", "ME") ,("OV", "ER")), start=Matrix.NB_LINES//2):
            for x, syllable in enumerate(word, start=Matrix.NB_COLS//2-1):
                color = self.matrix.cells[y][x]
                if color is None:
                    color = curses.COLOR_BLACK
                else:
                    color |= curses.A_REVERSE
                self.matrix.window.addstr(y, x*2+1, syllable, color)
        self.matrix.window.refresh()
        curses.beep()
        self.scr.timeout(-1)
        while self.scr.getkey() != self.controls["QUIT"]:
            pass
        self.stats.time = time.time() - self.stats.time
        self.quit()

    def quit(self):
        self.stats.save()
        t = time.localtime(time.time() - self.stats.time)
        self.music.stop()
        sys.exit(
            "SCORE\t{:n}\n".format(self.stats.score) +
            "HIGH\t{:n}\n".format(self.stats.high_score) +
            "TIME\t%02d:%02d:%02d\n" % (t.tm_hour-1, t.tm_min, t.tm_sec) +
            "LEVEL\t%d\n" % self.stats.level +
            "LINES\t%d" % self.stats.lines_cleared
        )


def main():
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] or "/?" in sys.argv[1:]:
        print(HELP_MSG)
    else:
        if "--reset" in sys.argv[1:] or "-r" in sys.argv[1:]:
            controls = ControlsParser()
            controls.reset()
            controls.edit()
        elif "--edit" in sys.argv[1:] or "-e" in sys.argv[1:]:
            ControlsParser().edit()
            
        locale.setlocale(locale.LC_ALL, '')
        if locale.getpreferredencoding() == 'UTF-8':
            os.environ["NCURSES_NO_UTF8_ACS"] = "1"
        curses.wrapper(Game)


if __name__ == "__main__":
    main()
