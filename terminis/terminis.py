# -*- coding: utf-8 -*-

import sys
try:
    import curses
except ImportError:
    print("This program requires curses.")
    print("You can install it on Windows with:")
    print("pip install --user windows-curses")
    sys.exit(1)
import random
import sched
import time
import os
import locale
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


DIR_NAME = "Terminis"
if sys.platform == "win32":
    DATA_PATH = os.environ.get("appdata", os.path.expanduser("~\Appdata\Roaming"))
    CONFIG_PATH = DATA_PATH
else:
    DATA_PATH = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    CONFIG_PATH = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
DATA_PATH = os.path.join(DATA_PATH, DIR_NAME)
CONFIG_PATH = os.path.join(CONFIG_PATH, DIR_NAME)
    
    
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
    

class Screen:

    def __enter__(self):
        self.scr = curses.initscr()
        curses.def_shell_mode()
        if curses.has_colors():
            self.init_colors()
        curses.noecho()
        curses.cbreak()
        self.scr.keypad(True)
        curses.curs_set(0)
        self.scr.clear()
        self.scr.nodelay(True)
        self.scr.leaveok(True)
        self.scr.getch()
        return self.scr
        if curses.has_colors():
            self.init_colors()
    
    def init_colors(self):
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

    def __exit__(self, type, value, traceback):
        curses.reset_shell_mode()
        curses.endwin()


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
        self.scheduler = matrix.game.scheduler
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
            self.scheduler.cancel(self.lock_timer)
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
        self.fall_timer = self.scheduler.enter(self.fall_delay, 2, self.fall, tuple())
        return self.move(Movement.DOWN)
    
    def locking(self):
        if not self.lock_timer:
            self.lock_timer = self.scheduler.enter(self.lock_delay, 1, self.lock, tuple())
            self.matrix.refresh()
            
    def postpone_lock(self):
        if self.lock_timer:
            self.scheduler.cancel(self.lock_timer)
            self.lock_timer = self.scheduler.enter(self.lock_delay, 1, self.lock, tuple())
            
    def lock(self):
        self.lock_timer = None
        if not self.move(Movement.DOWN, lock=False):
            if self.fall_timer:
                self.scheduler.cancel(self.fall_timer)
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
                for x, mino in enumerate(line):
                    if mino:
                        self.draw_mino(x, y, mino.color)
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
                self.cells[position.y][position.x] = mino
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
    FILE_PATH = os.path.join(DATA_PATH, FILE_NAME)
    
    def __init__(self, game, width, height, begin_x, begin_y, level):
        self.game = game
        self.width = width
        self.height = height
        self.level = level - 1
        self.goal = 0
        self.score = 0
        self.high_score = self.load_high_score()
        self.combo = -1
        self.time = time.time()
        self.lines_cleared = 0
        self.clock_timer = None
        self.strings = []
        locale.setlocale(locale.LC_ALL, '')
        Window.__init__(self, width, height, begin_x, begin_y)
        self.new_level()
        
    def load_high_score(self):
        try:
            with open(self.FILE_PATH, "r") as f:
               return int(f.read())
        except:
            return 0
        
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
        y0 = self.height - len(self.strings) - 2
        for y, string in enumerate(self.strings, start=y0):          
            x = (self.width-len(string)) // 2 + 1
            self.window.addstr(y, x, string)
        self.window.refresh()
        
    def clock(self):
        self.clock_timer = self.game.scheduler.enter(1, 3, self.clock, tuple())
        self.refresh()
        
            
    def new_level(self):
        self.level += 1
        if self.level <= 15:
            Tetromino.fall_delay = pow(0.8 - ((self.level-1)*0.007), self.level-1)
        else:
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
        if not os.path.exists(DATA_PATH):
            os.mkdir(DATA_PATH)
        try:
            with open(self.FILE_PATH, mode='w') as f:
                f.write(str(self.high_score))
        except Exception as e:
            print("High score could not be saved:")
            print(e)
        
        
class Config(Window, configparser.SafeConfigParser):
    TITLE = "CONTROLS"
    FILE_NAME = "config.cfg"
    FILE_PATH = os.path.join(CONFIG_PATH, FILE_NAME)
    
    def __init__(self, width, height, begin_x, begin_y):
        configparser.SafeConfigParser.__init__(self)
        self.optionxform = str
        self.add_section("CONTROLS")
        self.set("CONTROLS", "MOVE LEFT", "KEY_LEFT")
        self.set("CONTROLS", "MOVE RIGHT", "KEY_RIGHT")
        self.set("CONTROLS", "SOFT DROP", "KEY_DOWN")
        self.set("CONTROLS", "HARD DROP", "SPACE")
        self.set("CONTROLS", "ROTATE COUNTER", "KEY_UP")
        self.set("CONTROLS", "ROTATE CLOCKWISE", "ENTER")
        self.set("CONTROLS", "HOLD", "h")
        self.set("CONTROLS", "PAUSE", "p")
        self.set("CONTROLS", "QUIT", "q")
        if os.path.exists(self.FILE_PATH):
            self.read(self.FILE_PATH)
        else:
            if not os.path.exists(CONFIG_PATH):
                os.mkdir(CONFIG_PATH)
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
        for action, key in self.items("CONTROLS"):
            if key == "SPACE":
                self.set("CONTROLS", action, " ")
            elif key == "ENTER":
                self.set("CONTROLS", action, "\n")
            elif key == "TAB":
                self.set("CONTROLS", action, "\t")
    
    def refresh(self):
        self.draw_border()
        for y, (action, key) in enumerate(self.items("CONTROLS"), start=2):
            if key == " ":
                key = "SPACE"
            elif key == "\n":
                key = "ENTER"
            else:
                key = key.replace("KEY_", "")
                key = key.upper()
            self.window.addstr(y, 2, "%s\t%s" % (key, action.upper()))
        self.window.refresh()

class Game:
    WIDTH = 80
    HEIGHT = Matrix.HEIGHT
    
    def __init__(self, scr, level):
        self.scr = scr
        if curses.has_colors():
            self.init_colors()
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.scr.timeout(0)
        self.scr.getch()
        self.scheduler = sched.scheduler(time.time, self.process_input)
        self.random_bag = []
        left_x = (curses.COLS-self.WIDTH) // 2
        top_y = (curses.LINES-self.HEIGHT) // 2
        side_width = (self.WIDTH - Matrix.WIDTH) // 2
        side_height = self.HEIGHT - Hold.HEIGHT
        right_x = left_x + Matrix.WIDTH + side_width
        bottom_y = top_y + Hold.HEIGHT
        self.matrix = Matrix(self, left_x, top_y)
        self.hold = Hold(side_width, left_x, top_y)
        self.next = Next(side_width, right_x, top_y)
        self.next.piece = self.random_piece()(self.matrix, Next.PIECE_POSITION)
        self.stats = Stats(self, side_width, side_height, left_x, bottom_y, level)
        self.config = Config(side_width, side_height, right_x, bottom_y)
        self.do_action = {
            self.config.get("CONTROLS", "QUIT"): self.quit,
            self.config.get("CONTROLS", "PAUSE"): self.pause,
            self.config.get("CONTROLS", "HOLD"): self.swap,
            self.config.get("CONTROLS", "MOVE LEFT"): lambda: self.matrix.piece.move(Movement.LEFT),
            self.config.get("CONTROLS", "MOVE RIGHT"): lambda: self.matrix.piece.move(Movement.RIGHT),
            self.config.get("CONTROLS", "SOFT DROP"): lambda: self.matrix.piece.soft_drop(),
            self.config.get("CONTROLS", "ROTATE COUNTER"): lambda: self.matrix.piece.rotate(Rotation.COUNTERCLOCKWISE),
            self.config.get("CONTROLS", "ROTATE CLOCKWISE"): lambda: self.matrix.piece.rotate(Rotation.CLOCKWISE),
            self.config.get("CONTROLS", "HARD DROP"): lambda: self.matrix.piece.hard_drop()
        }
        self.playing = True
        self.paused = False
        self.new_piece()
        try:
            self.play()
        except KeyboardInterrupt:
            self.quit()
    
    def init_colors(self):
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
            self.matrix.piece.fall_timer = self.scheduler.enter(Tetromino.fall_delay, 2, self.matrix.piece.fall, tuple())
        else:
            self.over()
            
    def play(self):
        self.stats.time = time.time()
        self.stats.clock_timer = self.scheduler.enter(1, 3, self.stats.clock, tuple())
        while self.playing:
            self.scheduler.run()
                
    def process_input(self, delay):
        self.scr.timeout(int(1000*delay))
        try:
            self.do_action[self.scr.getkey()]()
        except (curses.error, KeyError):
            pass
            
    def pause(self):
        self.stats.time = time.time() - self.stats.time
        self.paused = True
        self.hold.refresh(paused=True)
        self.matrix.refresh(paused=True)
        self.next.refresh(paused=True)
        self.scr.timeout(-1)
        while True:
            key = self.scr.getkey()
            if key == self.config.get("CONTROLS", "QUIT"):
                self.quit()
                break
            elif key == self.config.get("CONTROLS", "PAUSE"):
                self.scr.nodelay(True)
                self.hold.refresh()
                self.matrix.refresh()
                self.next.refresh()
                self.stats.time = time.time() - self.stats.time
                break
            
    def swap(self):
        if self.matrix.piece.hold_enabled:
            if self.matrix.piece.fall_timer:
                self.scheduler.cancel(self.matrix.piece.fall_timer)
                self.matrix.piece.fall_timer = None
            if self.matrix.piece.lock_timer:
                self.scheduler.cancel(self.matrix.piece.lock_timer)
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
        while self.scr.getkey() != self.config.get("CONTROLS", "QUIT"):
            pass
        self.quit()
        
    def quit(self):
        self.playing = False
        if self.matrix.piece.fall_timer:
            self.scheduler.cancel(self.matrix.piece.fall_timer)
            self.matrix.piece.fall_timer = None
        if self.matrix.piece.lock_timer:
            self.scheduler.cancel(self.matrix.piece.lock_timer)
            self.matrix.piece.lock_timer = None
        if self.stats.clock_timer:
            self.scheduler.cancel(self.stats.clock_timer)
            self.stats.clock_timer = None
        self.stats.save()
        

def main():
    if len(sys.argv) >= 2:
        try:
            level = int(sys.argv[1])
        except ValueError:
            print("Usage:")
            print("python terminis.py [level]")
            print("  level: integer between 1 and 15")
            sys.exit(1)
        else:
            level = max(0, level)
            level = min(15, level)
    else:
        level = 1
    
    curses.wrapper(Game, level)
        
        
if __name__ == "__main__":
    main()
