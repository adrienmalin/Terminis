# -*- coding: utf-8 -*-

import random


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

    def __init__(self, matrix, position):
        self.position = position
        self.minoes_position = self.MINOES_POSITIONS
        self.orientation = 0
        self.rotation_point_5_used = False
        self.rotated_last = False
        self.hold_enabled = True
        
    def _possible_position(self, minoes_position, movement):
        potential_position = self.position + movement
        if all(
            self.matrix.is_free_cell(mino_position+potential_position)
            for mino_position in minoes_position
        ):
            return potential_position

    def _move(self, movement):
        possible_position = self._possible_position(self.minoes_position, movement)
        if possible_position:
            self.position = possible_position
            self.rotated_last = False
            return True
        else:
            return False
        
    def move_left(self):
        return self._move(Movement.LEFT)
        
    def move_right(self):
        return self._move(Movement.RIGHT)

    def soft_drop(self):
        if self._move(Movement.DOWN):
            return 1
        
    def fall(self):
        return self._move(Movement.DOWN)

    def hard_drop(self):
        lines = 0
        while self._move(Movement.DOWN, lock=False):
            lines += 2
        return lines

    def _rotate(self, direction):
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
        
    def rotate_clockwise(self):
        return self._rotate(Rotation.CLOCKWISE)
        
    def rotate_counterclockwise(self):
        return self._rotate(Rotation.COUNTERCLOCKWISE)

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

    def lock(self):
        t_spin = self.piece.t_spin()
        for mino_position in self.piece.minoes_position:
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
                self.cells.insert(0, [Mino.NO_MINO for x in range(self.NB_COLS)])
                nb_lines_cleared += 1
                
        return nb_lines_cleared, t_spin


class Hold:
    pass


class Next:
    pass


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

    def clock(self):
        self.clock_timer = scheduler.enter(1, 3, self.clock, tuple())
        self.refresh()

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
            os.makedirs(self.DIR_PATH)
        try:
            with open(self.FILE_PATH, mode='w') as f:
                f.write(str(self.high_score))
        except Exception as e:
            print("High score could not be saved:")
            print(e)


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
        self.next.piece = self.random_piece()
        self.start_next_piece()
        self.input_timer = scheduler.enter(self.AUTOREPEAT_DELAY, 2, self.process_input, tuple())

        try:
            scheduler.run()
        except KeyboardInterrupt:
            self.quit()

    def random_piece(self):
        if not self.random_bag:
            self.random_bag = list(self.TETROMINOES)
            random.shuffle(self.random_bag)
        return self.random_bag.pop()(self.matrix, Next.PIECE_POSITION)

    def start_next_piece(self):
        self.matrix.piece = self.next.piece
        self.next.piece = self.random_piece()
        self.next.refresh()
        self.start_piece()
            
    def start_piece(self):
        self.matrix.piece.position = Matrix.PIECE_POSITION
        if self.matrix.piece.possible_position(self.matrix.piece.minoes_position, Movement.STILL):
            self.matrix.piece.fall_timer = scheduler.enter(Tetromino.fall_delay, 2, self.matrix.piece.fall, tuple())
            self.matrix.refresh()
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
                self.matrix.piece.fall_timer = scheduler.cancel(self.matrix.piece.fall_timer)
            if self.matrix.piece.lock_timer:
                self.matrix.piece.lock_timer = scheduler.cancel(self.matrix.piece.lock_timer)
                
            self.matrix.piece, self.hold.piece = self.hold.piece, self.matrix.piece
            self.hold.piece.position = self.hold.PIECE_POSITION
            self.hold.piece.minoes_position = self.hold.piece.MINOES_POSITIONS
            self.hold.piece.hold_enabled = False
            self.hold.refresh()
            
            if self.matrix.piece:
                self.start_piece()
            else:
                self.start_next_piece()

    def over(self):
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
        self.quit()

    def quit(self):
        self.playing = False
        if self.matrix.piece.fall_timer:
            self.matrix.piece.fall_timer = scheduler.cancel(self.matrix.piece.fall_timer)
        if self.matrix.piece.lock_timer:
            self.matrix.piece.lock_timer = scheduler.cancel(self.matrix.piece.lock_timer)
        if self.stats.clock_timer:
            self.stats.clock_timer = scheduler.cancel(self.stats.clock_timer)
        if self.input_timer:
            self.input_timer = scheduler.cancel(self.input_timer)
        self.stats.save()
