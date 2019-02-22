# -*- coding: utf-8 -*-

import random
import time


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
    STILL = Point(0, 0)
    
    
class Mino:
    NO_MINO = 0
    I = 1
    J = 2
    L = 3
    O = 4
    S = 5
    T = 6
    Z = 7


class Tetromino:
    INIT_POSITION = Point(4, 0)
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

    def __init__(self, position):
        self.position = self.INIT_POSITION
        self.minoes_position = self.MINOES_POSITIONS
        self.orientation = 0
        self.rotation_point_5_used = False
        self.rotated_last = False
        self.hold_enabled = True

    def t_spin(self):
        return ""


class O(Tetromino):
    MINOES_POSITIONS = (Point(0, 0), Point(1, 0), Point(0, -1), Point(1, -1))
    MINOES_TYPE = Mino.O

    def _rotate(self, direction):
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
    MINOES_TYPE = Mino.I

class T(Tetromino):
    MINOES_POSITIONS = (Point(-1, 0), Point(0, 0), Point(0, -1), Point(1, 0))
    MINOES_TYPE = Mino.T
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
    MINOES_TYPE = Mino.L

class J(Tetromino):
    MINOES_POSITIONS = (Point(-1, -1), Point(-1, 0), Point(0, 0), Point(1, 0))
    MINOES_TYPE = Mino.J

class S(Tetromino):
    MINOES_POSITIONS = (Point(-1, 0), Point(0, 0), Point(0, -1), Point(1, -1))
    MINOES_TYPE = Mino.S

class Z(Tetromino):
    MINOES_POSITIONS = (Point(-1, -1), Point(0, -1), Point(0, 0), Point(1, 0))
    MINOES_TYPE = Mino.Z


class Matrix:
    NB_COLS = 10
    NB_LINES = 20
    PIECE_POSITION = Point(4, 0)

    def __init__(self):
        self.cells = [
            [Mino.NO_MINO for x in range(self.NB_COLS)]
            for y in range(self.NB_LINES)
        ]

    def is_free_cell(self, position):
        return (
            0 <= position.x < self.NB_COLS
            and position.y < self.NB_LINES
            and not (position.y >= 0 and self.cells[position.y][position.x] != Mino.NO_MINO)
        )

    def lock(self, piece):
        for mino_position in piece.minoes_position:
            position = mino_position + piece.position
            if position.y >= 0:
                self.cells[position.y][position.x] = piece.MINOES_TYPE
            else:
                return None
        else:
            nb_lines_cleared = 0
            for y, line in enumerate(self.cells):
                if all(mino for mino in line):
                    self.cells.pop(y)
                    self.cells.insert(0, [Mino.NO_MINO for x in range(self.NB_COLS)])
                    nb_lines_cleared += 1
            return nb_lines_cleared


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


class Game:
    AUTOREPEAT_DELAY = 0.02
    LOCK_DELAY = 0.5
    FALL_DELAY = 1
    TETROMINOES = (O, I, T, L, J, S, Z)
    SCORES = (
        {"name": "", "": 0, "MINI T-SPIN": 1, "T-SPIN": 4},
        {"name": "SINGLE", "": 1, "MINI T-SPIN": 2, "T-SPIN": 8},
        {"name": "DOUBLE", "": 3, "T-SPIN": 12},
        {"name": "TRIPLE", "": 5, "T-SPIN": 16},
        {"name": "TETRIS", "": 8}
    )

    def __init__(self, level=1):
        self.matrix = Matrix()
        self.paused = False
        self.start_next_piece()
        self.score = 0
        self.level = level - 1
        self.random_bag = []
        self.next_piece = self.random_piece()
        self.held_piece = None
        self.time = time.time()
        self.playing = True
        self.next_level()
        self.new_piece()

    def random_piece(self):
        if not self.random_bag:
            self.random_bag = list(self.TETROMINOES)
            random.shuffle(self.random_bag)
        return self.random_bag.pop()()

    def next_level(self):
        self.level += 1
        if self.level <= 20:
            self.fall_delay = pow(0.8 - ((self.level-1)*0.007), self.level-1)
        if self.level > 15:
            self.lock_delay = 0.5 * pow(0.9, self.level-15)
        self.goal += 5 * self.level

    def new_piece(self):
        self.current_piece, self.next_piece = self.next_piece, self.random_piece()
        self.start_piece()

    def hold_piece(self):
        if self.current_piece.hold_enabled:
            self.current_piece, self.hold_piece = self.held_piece, self.current_piece
            self.held_piece.minoes_position = self.held_piece.MINOES_POSITIONS
            self.held_piece.hold_enabled = False
            
            if self.matrix.piece:
                self.start_piece()
            else:
                self.new_piece()
            
    def start_piece(self):
        self.current_piece.position = self.current_piece.INIT_POSITION
        if not 
            self.over()
        
    def _possible_position(self, minoes_position, movement):
        potential_position = self.position + movement
        if all(
            self.matrix.is_free_cell(mino_position+potential_position)
            for mino_position in minoes_position
        ):
            return potential_position
        
    def piece_blocked(self):
        return not self.current_piece._possible_position(self.current_piece.minoes_position, Movement.STILL)

    def move(self, movement):
        possible_position = self._possible_position(self.minoes_position, movement)
        if possible_position:
            self.position = possible_position
            self.rotated_last = False
            return True
        else:
            return False

    def rotate(self, direction):
        potential_minoes_positions = tuple(
            Point(-direction*mino_position.y, direction*mino_position.x)
            for mino_position in self.minoes_position
        )
        for rotation_point, liberty_degree in enumerate(self.SUPER_ROTATION_SYSTEM[self.orientation][direction], start=1):
            possible_position = self._possible_position(potential_minoes_positions, liberty_degree)
            if possible_position:
                self.orientation = (self.orientation+direction) % 4
                self.position = possible_position
                self.minoes_position = potential_minoes_positions
                self.rotated_last = True
                if rotation_point == 5:
                    self.rotation_point_5_used = True
                return True
        
    def move_left(self):
        self.current_piece.move(Movement.LEFT)
        
    def move_right(self):
        self.current_piece.move(Movement.RIGHT)

    def soft_drop(self):
        if self.current_piece.move(Movement.DOWN):
            self.score += 1
        
    def fall(self):
        self.current_piece.move(Movement.DOWN)

    def hard_drop(self):
        while self.current_piece.move(Movement.DOWN):
            self.score += 2
        self.lock_piece()
        
    def rotate_clockwise(self):
        return self.current_piece.rotate(Rotation.CLOCKWISE)
        
    def rotate_counterclockwise(self):
        return self.current_piece.rotate(Rotation.COUNTERCLOCKWISE)

    def lock_piece(self):
        t_spin = self.current_piece.t_spin()
        nb_lines = self.matrix.lock(self.current_piece)
        
        if nb_lines is None:
            self.over()
            return
        
        if nb_lines:
            self.combo += 1
        else:
            self.combo = -1
            
        if nb_lines or t_spin:
            ds = self.SCORES[nb_lines][t_spin]
            self.goal -= ds
            ds *= 100 * self.level
            self.score += ds
            
        if self.combo >= 1:
            self.strings.append("COMBO x%d" % self.combo)
            ds = (20 if nb_lines==1 else 50) * self.combo * self.level
            self.score += ds
            self.strings.append(str(ds))
            
        if self.goal <= 0:
            self.new_level()
            
    def pause(self):
        self.time = time.time() - self.time
        self.paused = True
        
    def resume(self):
        self.time = time.time() - self.time
        self.paused = False

    def over(self):
        self.playing = False
