#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import json
import logging
import random
import webapp2

import numpy as np

# Reads json description of the board and provides simple interface.

BLACK = 1
WHITE = 2
BOARD_SIZE = 8

class Game:
    # Takes json or a board directly.
    def __init__(self, body=None, board=None):
        if body:
            game = json.loads(body)
            self._board = game["board"]
        else:
            self._board = board

    # Returns piece on the board.
    # 0 for no pieces, 1 for player 1, 2 for player 2.
    # None for coordinate out of scope.
    def Pos(self, x, y):
        return Pos(self._board["Pieces"], x, y)

    # Returns who plays next.
    def Next(self):
        return self._board["Next"]

    # Returns the array of valid moves for next player.
    # Each move is a dict
    #   "Where": [x,y]
    #   "As": player number
    def ValidMoves(self):
        moves = []
        for y in xrange(1, 9):
            for x in xrange(1, 9):
                move = {"Where": [x, y],
                        "As": self.Next()}
                if self.NextBoardPosition(move):
                    move['Where'] = [move['Where'][0] - 1, move['Where'][1] - 1]
                    moves.append(move)

        return moves

    # Helper function of NextBoardPosition.  It looks towards
    # (delta_x, delta_y) direction for one of our own pieces and
    # flips pieces in between if the move is valid. Returns True
    # if pieces are captured in this direction, False otherwise.
    def __UpdateBoardDirection(self, new_board, x, y, delta_x, delta_y):
        player = self.Next()
        opponent = 3 - player
        look_x = x + delta_x
        look_y = y + delta_y
        flip_list = []
        while Pos(new_board, look_x, look_y) == opponent:
            flip_list.append([look_x, look_y])
            look_x += delta_x
            look_y += delta_y
        if Pos(new_board, look_x, look_y) == player and len(flip_list) > 0:
            # there's a continuous line of our opponents
            # pieces between our own pieces at
            # [look_x,look_y] and the newly placed one at
            # [x,y], making it a legal move.
            SetPos(new_board, x, y, player)
            for flip_move in flip_list:
                flip_x = flip_move[0]
                flip_y = flip_move[1]
                SetPos(new_board, flip_x, flip_y, player)
            return True
        return False

    # Takes a move dict and return the new Game state after that move.
    # Returns None if the move itself is invalid.
    def NextBoardPosition(self, move):
        x = move["Where"][0]
        y = move["Where"][1]
        if self.Pos(x, y) != 0:
            # x,y is already occupied.
            return None
        new_board = copy.deepcopy(self._board)
        pieces = new_board["Pieces"]

        if not (self.__UpdateBoardDirection(pieces, x, y, 1, 0)
                | self.__UpdateBoardDirection(pieces, x, y, 0, 1)
                | self.__UpdateBoardDirection(pieces, x, y, -1, 0)
                | self.__UpdateBoardDirection(pieces, x, y, 0, -1)
                | self.__UpdateBoardDirection(pieces, x, y, 1, 1)
                | self.__UpdateBoardDirection(pieces, x, y, -1, 1)
                | self.__UpdateBoardDirection(pieces, x, y, 1, -1)
                | self.__UpdateBoardDirection(pieces, x, y, -1, -1)):
            # Nothing was captured. Move is invalid.
            return None

        # Something was captured. Move is valid.
        new_board["Next"] = 3 - self.Next()
        return Game(board=new_board)

# Returns piece on the board.
# 0 for no pieces, 1 for player 1, 2 for player 2.
# None for coordinate out of scope.
#
# Pos and SetPos takes care of converting coordinate from 1-indexed to
# 0-indexed that is actually used in the underlying arrays.


def Pos(board, x, y):
    if 1 <= x and x <= 8 and 1 <= y and y <= 8:
        return board[y - 1][x - 1]
    return None

# Set piece on the board at (x,y) coordinate


def SetPos(board, x, y, piece):
    if x < 1 or 8 < x or y < 1 or 8 < y or piece not in [0, 1, 2]:
        return False
    board[y - 1][x - 1] = piece

# Debug function to pretty print the array representation of board.


def PrettyPrint(board, nl="<br>"):
    s = ""
    for row in board:
        for piece in row:
            s += str(piece)
        s += nl
    return s


def PrettyMove(move):
    # m = move["Where"]
    m = move[:2]
    print(m)
    return '%s%d' % (chr(ord('A') + m[0] ), m[1] + 1)


class MainHandler(webapp2.RequestHandler):
    # Handling GET request, just for debugging purposes.
    # If you open this handler directly, it will show you the
    # HTML form here and let you copy-paste some game's JSON
    # here for testing.
    def get(self):
        if not self.request.get('json'):
            self.response.write("""
<body><form method=get>
Paste JSON here:<p/><textarea name=json cols=80 rows=24></textarea>
<p/><input type=submit>
</form>
</body>
""")
            return
        else:
            g = Game(self.request.get('json'))
            self.pickMove(g)

    def post(self):
        # Reads JSON representation of the board and store as the object.
        g = Game(self.request.body)
        # Do the picking of a move and print the result.
        self.pickMove(g)

    def pickMove(self, g):
        # Gets all valid moves.
        valid_moves = g.ValidMoves()
        if len(valid_moves) == 0:
            # Passes if no valid moves.
            self.response.write("PASS")
        else:
            # Chooses a valid move randomly if available.
            # TO STEP STUDENTS:
            # You'll probably want to change how this works, to do something
            # more clever than just picking a random move.

            move = self.bestMove(g._board, valid_moves, g)
            self.response.write(PrettyMove(move))

    def bestMove(self, board, valid_moves, game):
        '''
        input:
            - g: Game() object
            - valid_moves: sets of moves as {'WHERE':, 'AS': turn }
        return:
            - a move in string
        '''
        printBoard(board['Pieces'])

        # Convert to numpy array
        board_array = np.array(board['Pieces'])

        # current number of stone
        num_b = np.count_nonzero(board_array == 1)
        num_w = np.count_nonzero(board_array == 2)

        print("BLACK IS ", num_b)
        print("WHITE IS ", num_w)

        return MinMax(board['Next'], game, depth=3)


def printBoard(board):
    '''
    - Converts a Board into a human-readable ASCII art diagram.
    '''
    print("\n")
    print(" | A B C D E F G H|")
    print("-+----------------+")
    for y in range(8):
        print("%d|" % (y + 1)),
        for x in range(8):
            print(board[y][x]),
        print("|%d" % (y + 1))
    print("-+----------------+")
    print(" | A B C D E F G H|")


def evaluate(board, player):
    """
    - heuristic evaluation
    """
    score = 0
    curr_player = player

    board_array = np.array(board)

    # Current number for each
    opponent = WHITE if curr_player == BLACK else BLACK
    num_p = np.count_nonzero(board_array == player)
    num_o = np.count_nonzero(board_array == opponent)

    # Positions of each players' stone placed
    pos_p = np.argwhere(board_array == curr_player)
    pos_o = np.argwhere(board_array == opponent)

    if pos_p is not None:
        for coord in pos_p:

            coord = tuple(coord)

            # Check corner
            if coord in [(0, 0), (0, BOARD_SIZE - 1), (BOARD_SIZE - 1, 0), (BOARD_SIZE - 1, BOARD_SIZE - 1)]:
                score += 50
            # Check region4
            elif coord in [(0, 1), (1, 0), (1, 1), (BOARD_SIZE - 2, 0), (BOARD_SIZE - 1, 1), (BOARD_SIZE - 2, 1) ,\
                           (0, BOARD_SIZE - 2), (1, BOARD_SIZE - 1), (1, BOARD_SIZE - 2), \
                           (BOARD_SIZE - 1, BOARD_SIZE - 2), (BOARD_SIZE - 2, BOARD_SIZE - 1), (BOARD_SIZE - 2, BOARD_SIZE - 2)]:
                score += -10
            elif coord in [(0, 2), (0, 5), (2, 0), (2, 7), (5, 0), (5, 7), (7, 2), (7, 5)]:
                score += 30
            elif coord in [(0,3),(0,4),(3,0),(3,7),(4,0),(4,7),(7,3),(7,4)]:
                score += 20
            elif coord in [(1,2),(1,3),(1,4),(1,5),(2,1),(2,6),(3,1),(3,6),(4,1),(4,6),(5,1),(5,6),(6,2),(6,3),(6,4),(6,5)]:
                score +=1
            elif coord in [(2,2),(2,5),(5,2),(5,5)]:
                score+=4
            elif coord in [(2,3),(2,4),(3,2),(4,2),(3,5),(4,5),(5,3),(5,4)]:
                score+=3
            else:
                score+=2

    # Check if the player wins in the current states
    score+= 300 if num_p > num_o else -30

    return score



def MinMax(player, game, depth=3):
    """
    Depth: max 60
    """
    if player == BLACK:
        best = [-1, -1, -float('inf')]
    else:
        best = [-1, -1, float('inf')]

    if not depth:
        score = evaluate(game._board['Pieces'], player)
        return [-1, -1, score]
    # print(game.ValidMoves())
    for pos in game.ValidMoves():
        x, y = pos['Where']
        # SAVE
        temp = game._board['Pieces']
        game._board['Pieces'][x][y] = player
        next_p = WHITE if player == BLACK else BLACK
        # PERFORM FLIPS
        flipPieces(player, pos['Where'], game)
        score = MinMax(next_p, game, depth - 1)
        # REVRT g._board['Pieces'] to previous state
        game._board['Pieces'] = temp
        # game._board['Pieces'][x][y] = 0
        score[0], score[1] = x, y

        if player == BLACK:  # Max
            best = score if score[2] > best[2] else best
        else:
            best = score if score[2] < best[2] else best  # Min
    return best


def flipPieces(player, coord, game):
    '''
    Flip the pieces
    '''
    # checks all 8 direction
    directions = [(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1),(0,1)]
    flips = (flip for direction in directions
                      for flip in _getFlips(tuple(coord), direction, player, game))

    for x,y in flips:
        game._board['Pieces'][x][y] = player


def _getFlips(origin, direction, player, game):
    '''
    Returns a list of all possible flips position
    '''
    flips = [origin]
    opponent = WHITE if player == BLACK else BLACK
    for x, y in _incrementMove(origin, direction):
        if game._board['Pieces'][x][y] == opponent:
            flips.append((x, y))
        elif game._board['Pieces'][x][y] == 0:
            break
        elif game._board['Pieces'][x][y] == player and len(flips) > 1:
            return flips
    return []

def _incrementMove(move, direction):
    """
    - return valid position
    """
    move = map(sum, zip(move, direction))
    while all(map(lambda x: 0 <= x < 8, move)):
        yield move
        move = map(sum, zip(move, direction))

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
