# %% Imports
import numpy as np


# %% Constants
files = ["a", "b", "c", "d", "e", "f", "g", "h"]
ranks = ["1", "2", "3", "4", "5", "6", "7", "8"]


class MoveError(Exception):
    pass


def getRelativeLoc(color, loc, addRank, addFile):
    """Return the name of a cell that is the specified increment from loc.
    Always is from the perspective of the specified color, so black +1 rank is closer to 1
    """
    if color == "b":
        mult = -1
    else:
        mult = 1

    locFile = loc[0]
    locRank = loc[1]
    relRank = str(int(locRank) + addRank * mult)
    relFile = chr(ord(locFile) + addFile * mult)
    return relFile + relRank


def getOtherColor(c):
    if c == "w":
        return "b"
    return "w"


def isInCheck(board: dict, color: str) -> bool:
    """Given a board layout, returns bool if specified color is in check

    Args:

        board (dict) -- keys are squares, values are pieces

        color (str) -- w or b

    Returns:

        bool -- is color in check in board?
    """
    otherColor = getOtherColor(color)
    # Get piece location from
    for p in board:
        # print(self.board[p])
        if str(board[p]) == color + "K":
            k = p
            print(f"{color}K is at {p}")

    # If a pawn is on a previous rank and adjacent file, return yes
    pawnAttackSquares = [
        getRelativeLoc(color, k, 1, _)
        for _ in [1, -1]
        if getRelativeLoc(color, k, 1, _) in board.keys()
    ]
    for s in pawnAttackSquares:
        if str(board[s]) == otherColor + "P":
            return True

    # Knights being 2,1 or 1,2 +/- on both away means check
    knightAttackSquares = [
        getRelativeLoc(color, k, r * rankMult, f * fileMult)
        for r, f in zip([1, 2], [2, 1])
        for rankMult in [-1, 1]
        for fileMult in [-1, 1]
        if getRelativeLoc(color, k, r * rankMult, f * fileMult) in board.keys()
    ]
    for s in knightAttackSquares:
        if str(board[s]) == otherColor + "N":
            return True

    # Check that closest diagonal piece isn't bishop or Queen
    diagonals = [getDiagonal(board, color, k, i, j) for i in [-1, 1] for j in [-1, 1]]
    for diag in diagonals:
        for s in diag:
            if str(board[s]) == "  ":
                pass
            if str(board[s]) in [otherColor + "Q", otherColor + "B"]:
                return True

    # Check that closest straight line piece isn't rook or Queen
    straights = [
        getStraight(board, color, k, i * mult, j * mult)
        for i, j in zip([0, 1], [1, 0])
        for mult in [-1, 1]
    ]
    for straight in straights:
        for s in straight:
            if str(board[s]) == "  ":
                pass
            if str(board[s]) in [otherColor + "Q", otherColor + "R"]:
                return True


def getDiagonal(board, color, loc, rankDir=1, fileDir=1):
    out = [
        getRelativeLoc(color, loc, addRank=(i + 1) * rankDir, addFile=(i + 1) * fileDir)
        for i in range(7)
        if getRelativeLoc(
            color, loc, addRank=(i + 1) * rankDir, addFile=(i + 1) * fileDir
        )
        in board.keys()
    ]
    return out


def getStraight(board, color, loc, rankDir=0, fileDir=1):
    out = [
        getRelativeLoc(color, loc, addRank=(i + 1) * rankDir, addFile=(i + 1) * fileDir)
        for i in range(7)
        if getRelativeLoc(
            color, loc, addRank=(i + 1) * rankDir, addFile=(i + 1) * fileDir
        )
        in board.keys()
    ]
    return out


# %% Chess game class
class chessGame(object):
    "High-level object to store chess game state"

    def __init__(self):
        # Create chess board, load up pieces
        self.board = {}
        for f in files:
            for r in ranks:
                self.board[f + r] = self.empty()
        for r, color in (["1", "w"], ["8", "b"]):
            for _ in ["a" + r, "h" + r]:
                self.board[_] = self.piece(color, "R")
            for _ in ["b" + r, "g" + r]:
                self.board[_] = self.piece(color, "N")
            for _ in ["c" + r, "f" + r]:
                self.board[_] = self.piece(color, "B")
            self.board["d" + r] = self.piece(color, "Q")
            self.board["e" + r] = self.piece(color, "K")
            for f in files:
                pawnRank = ["2", "7"][color == "b"]
                self.board[f + pawnRank] = self.piece(color, "P")

        # Set other things about game
        self._toMove = "w"
        self._waiting = "b"

    def _changeTurn(self):
        if self._toMove == "w":
            self._toMove = "b"
            self._waiting = "w"
        else:
            self._toMove = "w"
            self._waiting = "b"

    def move(self, old, new):

        movingPiece = self.board[old]
        # Only move if its your turn
        if movingPiece.color != self._toMove:
            raise MoveError(f"It is {self._toMove} turn")
        print(f"Moving {movingPiece} from {old}->{new}")
        # Remove from from, place in to
        newBoard = self.board.copy()
        newBoard[new] = movingPiece
        newBoard[old] = self.empty()

        # Move is invalid if it results in moving color being in check
        if isInCheck(newBoard, self._toMove):
            raise MoveError(f"Move results in {self._toMove} in check")

        self.board = newBoard
        self._changeTurn()

        # print(newBoard[getRelativeLoc(color, k, 1, 1)])
        # print(newBoard[getRelativeLoc(color, k, 1, -1)])
        # print(f"Looking for {self._waiting}P")
        # if (newBoard[getRelativeLoc(color, k, 1, 1)] == self._waiting + "P") | (
        #     newBoard[getRelativeLoc(color, k, 1, -1)] == self._waiting + "P"
        # ):
        #     print('In check!')
        #     return True

    class piece(object):
        def __init__(self, color, name):
            assert color in ["b", "w"], "Invalid color"
            assert name in ["K", "Q", "B", "N", "R", "P"], "Invalid name"
            self.color = color
            self.name = name
            self.moveCnt = 0

        def __repr__(self):
            return self.color + self.name

        def getLegalMoves(self, loc, board):
            print(f"Getting legal moves for {self}")

    class empty(object):
        def __init__(self):
            pass

        def __repr__(self) -> str:
            return "  "

    def __repr__(self):
        out = ""
        out += f"\n{self._toMove} to move"
        out += "\n  -----------------------------------------"
        for r in [str(8 - x) for x in range(8)]:
            out += f"\n{r} |"
            for f in files:
                out += f" {self.board[f+r]} |"
            out += "\n  -----------------------------------------"
        out += "\n    a    b    c    d    e    f    g    h"

        return out


# %% Main
if __name__ == "__main__":
    game = chessGame()
    # print(game)
    game.move("e1", "h7")

    # game.move("g8", "g6")
    # game.move("e5", "e4")
    # print(game)
    # game.move("c8", "d7")
    print(game)

# %%
