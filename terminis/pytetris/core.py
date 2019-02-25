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
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Movement:
    LEFT  = Point(-1, 0)
    RIGHT = Point(1, 0)
    DOWN  = Point(0, 1)
    
    
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
    INIT_POSITION = Point(4, -1)
    LOCK_DELAY = 0.5

    def __init__(self):
        self.position = self.INIT_POSITION
        self.minoes_positions = self.MINOES_POSITIONS
        self.orientation = 0
        self.rotation_point_5_used = False
        self.rotated_last = False
        self.hold_enabled = True
        self.prelocked = False

    def t_spin(self):
        return ""


class O(Tetromino):
    MINOES_POSITIONS = (Point(0, 0), Point(1, 0), Point(0, -1), Point(1, -1))
    MINOES_TYPE = Mino.O
    SUPER_ROTATION_SYSTEM = (tuple(),)

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


class Tetris:
    TETROMINOES = (O, I, T, L, J, S, Z)
    LEN_NEXT_QUEUE = 1
    MATRIX_ROWS = 20
    MATRIX_COLS = 10
    INIT_POSITION = Point(4, 0)
    FALL_DELAY = 1
    LOCK_DELAY = 0.5
    AUTOSHIFT_DELAY = 0.2
    INIT_POSITION = Point(4, -1)
    SCORES = (
        {"name": "",       "": 0, "MINI T-SPIN": 1, "T-SPIN": 4},
        {"name": "SINGLE", "": 1, "MINI T-SPIN": 2, "T-SPIN": 8},
        {"name": "DOUBLE", "": 3, "T-SPIN": 12},
        {"name": "TRIPLE", "": 5, "T-SPIN": 16},
        {"name": "TETRIS", "": 8}
    )
    
    def __init__(self, high_score=0):
        self.high_score = high_score

    def _random_piece(self):
        if not self.random_bag:
            self.random_bag = list(self.TETROMINOES)
            random.shuffle(self.random_bag)
        return self.random_bag.pop()()
        
    def new_game(self, level=1):
        self.matrix = [
            [Mino.NO_MINO for x in range(self.MATRIX_COLS)]
            for y in range(self.MATRIX_ROWS)
        ]
        self.level = level - 1
        self.goal = 0
        self.score = 0
        self.random_bag = []
        self.next_queue = [
            self._random_piece()
            for _ in range(self.LEN_NEXT_QUEUE)
        ]
        self.held_piece = None
        self.fall_delay = self.FALL_DELAY
        self.lock_delay = self.LOCK_DELAY
        self.time = time.time()
        self.next_level()
        self.current_piece = None
        self.new_piece()

    def next_level(self):
        self.level += 1
        if self.level <= 20:
            self.fall_delay = pow(0.8 - ((self.level-1)*0.007), self.level-1)
        if self.level > 15:
            self.lock_delay = 0.5 * pow(0.9, self.level-15)
        self.goal += 5 * self.level
        self.show_text("LEVEL %d" % self.level)

    def new_piece(self):
        if not self.current_piece:
            self.current_piece = self.next_queue.pop(0)
            self.next_queue.append(self._random_piece())
        self.current_piece.position = self.INIT_POSITION
        if not self._move(Movement.DOWN):
            self.game_over()

    def hold_piece(self):
        if self.current_piece.hold_enabled:
            self.current_piece, self.hold_piece = self.held_piece, self.current_piece
            self.held_piece.minoes_positions = self.held_piece.MINOES_POSITIONS
            self.held_piece.hold_enabled = False
            self.new_piece()
            
    def _move_rotate(self, movement, minoes_positions):
        potential_position = self.current_piece.position + movement
        if all(
            self.is_free_cell(potential_position+mino_position)
            for mino_position in minoes_positions
        ):
            self.position = potential_position
            if self.current_piece.prelocked:
                self.postpone_lock()
            return True
        else:
            return False

    def _move(self, movement):
        if self._move_rotate(movement, self.current_piece.minoes_positions):
            self.current_piece.rotated_last = False
            return True
        else:
            if movement == Movement.DOWN and not self.current_piece.prelocked:
                self.prelock()
            return False

    def _rotate(self, direction):
        rotated_minoes_positions = tuple(
            Point(-direction*mino_position.y, direction*mino_position.x)
            for mino_position in self.current_piece.minoes_positions
        )
        for rotation_point, liberty_degree in enumerate(self.current_piece.SUPER_ROTATION_SYSTEM[self.current_piece.orientation][direction], start=1):
            potential_position = self.position + liberty_degree
            if self._move_rotate(potential_position, rotated_minoes_positions):
                self.current_piece.orientation = (self.current_piece.orientation+direction) % 4
                self.current_piece.minoes_position = rotated_minoes_positions
                self.current_piece.rotated_last = True
                if rotation_point == 5:
                    self.current_piece.rotation_point_5_used = True
                return True
        else:
            return False
        
    def move_left(self):
        self._move(Movement.LEFT)
        
    def move_right(self):
        self._move(Movement.RIGHT)

    def soft_drop(self):
        if self._move(Movement.DOWN):
            self.rows_dropped(1)

    def hard_drop(self):
        points = 0
        while self._move(Movement.DOWN):
            points += 2
        self.rows_dropped(points)
        self.lock_piece()
            
    def rows_dropped(self, points):
        self.update_score(points, "")
        
    def fall(self):
        self._move(Movement.DOWN)
        
    def rotate_clockwise(self):
        return self._rotate(Rotation.CLOCKWISE)
        
    def rotate_counterclockwise(self):
        return self._rotate(Rotation.COUNTERCLOCKWISE)

    def is_free_cell(self, position):
        return (
            0 <= position.x < self.MATRIX_COLS
            and position.y < self.MATRIX_ROWS
            and not (position.y >= 0 and self.matrix[position.y][position.x] != Mino.NO_MINO)
        )
        
    def prelock(self):
        """
        Schedules self.lock in self.lock_delay
        """
        raise NotImplementedError
    
    def postpone_lock(self):
        """
        Reset timer calling self.lock to self.lock_delay
        """
        raise NotImplementedError

    def lock_piece(self):
        if self.shape_fits(self.current_piece.position+Movement.DOWN, self.current_piece.minoes_positions):
            self.postpone_lock()
            return
        
        t_spin = self.current_piece.t_spin()
        
        for mino_position in self.current_piece.minoes_position:
            position = mino_position + self.current_piece.position
            if position.y >= 0:
                self.matrix[position.y][position.x] = self.current_piece.MINOES_TYPE
            else:
                self.game_over()
                return
            
        nb_rows = 0
        for y, row in enumerate(self.cells):
            if all(mino for mino in row):
                self.cells.pop(y)
                self.cells.insert(0, [Mino.NO_MINO for x in range(self.NB_COLS)])
                nb_rows += 1
        self.current_piece = None
        self.piece_locked(nb_rows, t_spin)

        if t_spin or nb_rows:
            points = self.SCORES[nb_rows][t_spin]
            self.goal -= points
            points *= 100 * self.level
            text = t_spin
            if t_spin and nb_rows:
                text += " "
            if nb_rows:
                text += self.SCORES[nb_rows]["name"]
            self.update_score(points, text)
            
        self.combo = self.combo + 1 if nb_rows else -1
        if self.combo >= 1:
            points = (20 if nb_rows==1 else 50) * self.combo * self.level
            text = "COMBO x%d" % self.combo
            self.update_score(points, text)
        
        if self.goal <= 0:
            self.new_level()
            
        self.new_piece()
            
    def update_score(self, points, text):
        self.score += points
        if self.score > self.high_score:
            self.high_score = self.score
        self.show_text("%s\n%d" % (text, points))
        
    def show_text(self, text):
        print(text)
            
    def pause(self):
        self.time = time.time() - self.time
        
    def resume(self):
        self.time = time.time() - self.time

    def game_over(self):
        self.show_text("GAME OVER")
