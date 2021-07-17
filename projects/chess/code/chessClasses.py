# %% Imports
from typing import List
import numpy as np


# %% Constants
FILES = ["a", "b", "c", "d", "e", "f", "g", "h"]
RANKS = ["1", "2", "3", "4", "5", "6", "7", "8"]
SQUARES = [f + r for f in FILES for r in RANKS]


class MoveError(Exception):
    "Generic error for move errors"
    pass


def getRelativeLoc(color: str, loc: str, addRank: int, addFile: int) -> str:
    """Return the name of a cell that is the specified increment from loc.
    Always is from the perspective of the specified color, so black +1 rank is closer to 1

    Args:

        color (str) -- w or b

        loc (str) -- location, like a1, g2, f8, etc.

        addRank (int) -- how many ranks to increment

        addFile (int) -- how many files to increment

    Returns:

        str -- initial location + specified ranks + files
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


def getOtherColor(c: str) -> str:
    "Returns the other color of w or b"
    assert c in ["w", "b"], f"Invalid color {c}"
    if c == "w":
        return "b"
    return "w"


def getLineFrom(
    color: str, loc: str, rankIncrement: int, fileIncrement: int
) -> List[str]:
    """Returns an incremental line from specified location.

    Args:

        color (str) -- b or w

        loc (str) -- a square like a1, g5, f8

        rankIncrement (int) -- what to add each iteration to the rank

        fileIncrement (int) -- what to add each iteration to the file

    Returns:

    list(str) -- the squares eminating in the specified vector from loc.

    Example:

    From a1, we can set a rankIncrement of 1 and a fileIncrement of 0 to get the a-file

    From c3, we can set a rank and file increment of -1 to get ['b2', 'a1']

    """
    out = [
        getRelativeLoc(
            color, loc, addRank=(i + 1) * rankIncrement, addFile=(i + 1) * fileIncrement
        )
        for i in range(7)
        if getRelativeLoc(
            color, loc, addRank=(i + 1) * rankIncrement, addFile=(i + 1) * fileIncrement
        )
        in SQUARES
    ]
    return out


def isInCheck(board: dict, color: str) -> bool:
    """Given a board layout, returns if specified color is in check

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
        if getRelativeLoc(color, k, 1, _) in SQUARES
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
        if getRelativeLoc(color, k, r * rankMult, f * fileMult) in SQUARES
    ]
    for s in knightAttackSquares:
        if str(board[s]) == otherColor + "N":
            return True

    # Check that closest diagonal piece isn't bishop or Queen
    diagonals = [getLineFrom(color, k, i, j) for i in [-1, 1] for j in [-1, 1]]
    for diag in diagonals:
        for s in diag:
            if str(board[s]) == "  ":
                pass
            if str(board[s]) in [otherColor + "Q", otherColor + "B"]:
                return True

    # Check that closest straight line piece isn't rook or Queen
    straights = [
        getLineFrom(color, k, i * mult, j * mult)
        for i, j in zip([0, 1], [1, 0])
        for mult in [-1, 1]
    ]
    for straight in straights:
        for s in straight:
            if str(board[s]) == "  ":
                pass
            if str(board[s]) in [otherColor + "Q", otherColor + "R"]:
                return True


# %% Chess game class
class chessGame(object):
    "High-level object to store chess game state"

    def __init__(self):
        # Create chess board, load up pieces
        self.board = {}
        for f in FILES:
            for r in RANKS:
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
            for f in FILES:
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

    def _isPiece(self, itm):
        "Is the itm a piece class?"
        return type(itm) == self.piece

    def move(self, old: str, new: str):
        "Execute specified move from old to new"

        movingPiece = self.board[old]

        # Ensure we are only moving pieces
        if not self._isPiece(itm=movingPiece):
            raise MoveError("Must move a piece")

        # Only move if its your turn
        if movingPiece.color != self._toMove:
            raise MoveError(f"It is {self._toMove} turn")
        print(f"Moving {movingPiece} from {old}->{new}")

        # Remove from from, place in to
        newBoard = self.board.copy()
        newBoard[new] = movingPiece
        newBoard[old] = self.empty()

        # Move is invalid if it results in moving color being in check
        if isInCheck(board=newBoard, color=self._toMove):
            raise MoveError(f"Move results in {self._toMove} in check")

        self.board = newBoard
        self._changeTurn()

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
        for r in reversed(RANKS):
            out += f"\n{r} |"
            for f in FILES:
                out += f" {self.board[f+r]} |"
            out += "\n  -----------------------------------------"
        out += "\n    a    b    c    d    e    f    g    h"

        return out


# %% Main
if __name__ == "__main__":
    game = chessGame()
    # print(game)
    game.move("e1", "e2")

    # game.move("g8", "g6")
    # game.move("e5", "e4")
    # print(game)
    # game.move("c8", "d7")
    print(game)

# %%
