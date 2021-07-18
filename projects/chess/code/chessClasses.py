# %% Imports
from typing import List
import pandas as pd


# %% Constants
FILES = ["a", "b", "c", "d", "e", "f", "g", "h"]
RANKS = ["1", "2", "3", "4", "5", "6", "7", "8"]
SQUARES = [f + r for f in FILES for r in RANKS]

# %% Lower-level classes
class MoveError(Exception):
    "Generic error for move errors"
    pass


class empty(object):
    "Empty square of board"

    def __init__(self):
        pass

    def __repr__(self) -> str:
        return "  "


class piece(object):
    def __init__(self, color, name):
        assert color in ["b", "w"], "Invalid color"
        assert name in ["K", "Q", "B", "N", "R", "P"], "Invalid name"
        self.color = color
        self.name = name
        self.moveCnt = 0

    def __repr__(self):
        return self.color + self.name


# %% Functions
def isPiece(p):
    "Is p of type piece?"
    return type(p) == piece


def getKingSquare(board: dict, color: str):
    "Returns the square in which the king is located"

    for s in board:
        if str(board[s]) == color + "K":
            return s

    raise ValueError("No square")


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


def getKnightAttackSquares(loc):
    out = [
        getRelativeLoc("w", loc, r * rankMult, f * fileMult)
        for r, f in zip([1, 2], [2, 1])
        for rankMult in [-1, 1]
        for fileMult in [-1, 1]
        if getRelativeLoc("w", loc, r * rankMult, f * fileMult) in SQUARES
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
    # Get king square
    otherColor = getOtherColor(color)
    k = getKingSquare(board, color)

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
    knightAttackSquares = getKnightAttackSquares(k)
    for s in knightAttackSquares:
        if str(board[s]) == otherColor + "N":
            return True

    # Check that closest diagonal piece isn't bishop or Queen
    diagonals = [getLineFrom(color, k, i, j) for i in [-1, 1] for j in [-1, 1]]
    for diag in diagonals:
        for s in diag:
            if type(board[s]) == empty:
                pass
            elif str(board[s])[0] == color:
                break
            elif str(board[s]) in [otherColor + "Q", otherColor + "B"]:
                return True
            else:
                break

    # Check that closest straight line piece isn't rook or Queen
    straights = [
        getLineFrom(color, k, i * mult, j * mult)
        for i, j in zip([0, 1], [1, 0])
        for mult in [-1, 1]
    ]
    for straight in straights:
        for s in straight:
            if type(board[s]) == empty:
                pass
            elif str(board[s])[0] == color:
                break
            elif str(board[s]) in [otherColor + "Q", otherColor + "R"]:
                return True
            else:
                break


def getPotentialValidMoves(board, currSquare, prevMoves):
    "Returns all moves for a piece REGARDLESS of if they leave the moving color in check"

    movingPiece = board[currSquare]
    movingColor = movingPiece.color
    diagonals = [
        getLineFrom(
            color=movingColor,
            loc=currSquare,
            rankIncrement=i,
            fileIncrement=j,
        )
        for i in [-1, 1]
        for j in [-1, 1]
    ]
    straights = [
        getLineFrom(
            color=movingColor,
            loc=currSquare,
            rankIncrement=i * mult,
            fileIncrement=j * mult,
        )
        for i, j in zip([0, 1], [1, 0])
        for mult in [-1, 1]
    ]
    move = {"piece": str(movingPiece), "oldSquare": currSquare, "special": None}

    # King squares
    potentialValidMoves = []
    if movingPiece.name == "K":
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                newLoc = getRelativeLoc(
                    color=movingColor, loc=currSquare, addRank=i, addFile=j
                )
            if newLoc not in SQUARES:
                continue
            if newLoc == currSquare:
                continue
            if str(board[newLoc])[0] == movingColor:
                continue
            potentialValidMoves.append({**move, "newSquare": newLoc})

        # Short castling - if h-file rook has 0 moves, king has 0 moves, squares between are empty
        if movingPiece.moveCnt != 0:
            pass

        elif str(board[getRelativeLoc("w", currSquare, 0, 3)]) != movingColor + "R":
            pass
        elif board[getRelativeLoc("w", currSquare, 0, 3)].moveCnt != 0:
            pass
        elif type(board[getRelativeLoc("w", currSquare, 0, 1)]) == piece:
            pass
        elif type(board[getRelativeLoc("w", currSquare, 0, 2)]) == piece:
            pass
        else:
            potentialValidMoves.append(
                {
                    **move,
                    "newSquare": getRelativeLoc("w", currSquare, 0, 2),
                    "special": "shortCastle",
                }
            )

        # long castling - if a-file rook has 0 moves, king has 0 moves, squares between are empty
        if movingPiece.moveCnt != 0:
            pass
        elif str(board[getRelativeLoc("w", currSquare, 0, -4)]) != movingColor + "R":
            pass
        elif board[getRelativeLoc("w", currSquare, 0, -4)].moveCnt != 0:
            pass
        elif type(board[getRelativeLoc("w", currSquare, 0, -1)]) == piece:
            pass
        elif type(board[getRelativeLoc("w", currSquare, 0, -2)]) == piece:
            pass
        elif type(board[getRelativeLoc("w", currSquare, 0, -3)]) == piece:
            pass
        else:
            potentialValidMoves.append(
                {
                    **move,
                    "newSquare": getRelativeLoc("w", currSquare, 0, -2),
                    "special": "longCastle",
                }
            )

    # Queen squares
    if movingPiece.name == "Q":
        for line in straights + diagonals:
            for s in line:
                currOccupant = board[s]
                if type(currOccupant) == empty:
                    potentialValidMoves.append({**move, "newSquare": s})
                elif currOccupant.color == movingColor:
                    break
                else:
                    potentialValidMoves.append({**move, "newSquare": s})
                    break

    # Rook squares
    if movingPiece.name == "R":
        for line in straights:
            for s in line:
                currOccupant = board[s]
                if type(currOccupant) == empty:
                    potentialValidMoves.append({**move, "newSquare": s})
                elif currOccupant.color == movingColor:
                    break
                else:
                    potentialValidMoves.append({**move, "newSquare": s})
                    break

    # Bishop squares
    if movingPiece.name == "B":
        for line in diagonals:
            for s in line:
                currOccupant = board[s]
                if type(currOccupant) == empty:
                    potentialValidMoves.append({**move, "newSquare": s})
                elif currOccupant.color == movingColor:
                    break
                else:
                    potentialValidMoves.append({**move, "newSquare": s})
                    break

    # Knight squares
    if movingPiece.name == "N":
        for s in getKnightAttackSquares(currSquare):
            currOccupant = board[s]
            if type(currOccupant) == empty:
                potentialValidMoves.append({**move, "newSquare": s})
            elif currOccupant.color != movingColor:
                potentialValidMoves.append({**move, "newSquare": s})

    # Pawn squares
    if movingPiece.name == "P":
        # if 1 square ahead is empty, that is allowed, check two ahead
        oneAhead = getRelativeLoc(movingColor, currSquare, 1, 0)
        if type(board[oneAhead]) == empty:
            potentialValidMoves.append({**move, "newSquare": oneAhead})

            # If piece move count == 0 then two ahead is allowed if its not a piece
            twoAhead = getRelativeLoc(movingColor, currSquare, 2, 0)
            if movingPiece.moveCnt == 0:
                if type(board[twoAhead]) == empty:
                    potentialValidMoves.append({**move, "newSquare": twoAhead})

        # Takes one rank and +/1 1 file
        takeSquares = [
            getRelativeLoc(movingColor, currSquare, 1, fileOffset)
            for fileOffset in [-1, 1]
            if getRelativeLoc(movingColor, currSquare, 1, fileOffset) in board.keys()
        ]
        for takeSquare in takeSquares:
            if type(board[takeSquare]) == piece:
                if board[takeSquare].color != movingColor:
                    potentialValidMoves.append({**move, "newSquare": takeSquare})
        # en passant logic
        # If prevmove was two squares forward and one square back was takeable is square in takeSquares?
        if len(prevMoves) == 0:  # first move can't be en passant
            pass
        else:
            prevMove = prevMoves[-1]
            otherColor = getOtherColor(movingColor)
            prevMoveOneSquareBack = getRelativeLoc(
                otherColor, prevMove["newSquare"], -1, 0
            )
            if prevMove["piece"] != otherColor + "P":  # If prevmove not pawn
                pass
            elif (
                int(prevMove["newSquare"][1]) - int(prevMove["oldSquare"][1]) != 2
            ):  # prevmove wasnt two squares
                pass
            elif prevMoveOneSquareBack not in takeSquares:  # Wasn't take opp
                pass
            else:
                potentialValidMoves.append(
                    {**move, "newSquare": prevMoveOneSquareBack, "special": "enpassant"}
                )

    return potentialValidMoves


def getNewBoard(board: dict, move: dict) -> dict:
    "Returns what the new board would look like after move is executed"
    newBoard = board.copy()

    movingPiece = board[move["oldSquare"]]
    movingColor = movingPiece.color

    if move["piece"] != str(movingPiece):
        raise MoveError(
            f"Square {move['oldSquare']} does not have piece {move['piece']}"
        )
    newBoard[move["newSquare"]] = movingPiece
    newBoard[move["oldSquare"]] = empty()

    if move["special"] == "enpassant":
        newBoard[getRelativeLoc(movingColor, move["newSquare"], -1, 0)] = empty()
    if move["special"] == "shortCastle":
        newBoard[getRelativeLoc("w", move["newSquare"], 0, -1)] = newBoard[
            getRelativeLoc("w", move["newSquare"], 0, 1)
        ]
        newBoard[getRelativeLoc("w", move["newSquare"], 0, 1)] = empty()
    if move["special"] == "longCastle":
        newBoard[getRelativeLoc("w", move["newSquare"], 0, 1)] = newBoard[
            getRelativeLoc("w", move["newSquare"], 0, -2)
        ]
        newBoard[getRelativeLoc("w", move["newSquare"], 0, -2)] = empty()

    return newBoard


def getValidMoves(board: dict, color: str, prevMoves: List[dict]) -> list:
    "Gets all valid moves for a specific color. If list length = 0, checkmate!"
    potentialValidMoves = []
    validMoves = []
    for currSquare in board:
        if type(board[currSquare]) == empty:
            continue

        movingPiece = board[currSquare]
        if str(movingPiece)[0] != color:
            continue

        potentialValidMoves += getPotentialValidMoves(board, currSquare, prevMoves)
    for move in potentialValidMoves:
        if isInCheck(getNewBoard(board, move), color):
            continue

        validMoves.append(move)

    return validMoves


# %% Chess game class
class chessGame(object):
    "High-level object to store chess game state"

    def __init__(self):
        # Create chess board, load up pieces
        self.board = {}
        for f in FILES:
            for r in RANKS:
                self.board[f + r] = empty()
        for r, color in (["1", "w"], ["8", "b"]):
            for _ in ["a" + r, "h" + r]:
                self.board[_] = piece(color, "R")
            for _ in ["b" + r, "g" + r]:
                self.board[_] = piece(color, "N")
            for _ in ["c" + r, "f" + r]:
                self.board[_] = piece(color, "B")
            self.board["d" + r] = piece(color, "Q")
            self.board["e" + r] = piece(color, "K")
            for f in FILES:
                pawnRank = ["2", "7"][color == "b"]
                self.board[f + pawnRank] = piece(color, "P")

        # Set other things about game
        self._toMove = "w"
        self._waiting = "b"
        self._moves = []

    def _changeTurn(self):
        if self._toMove == "w":
            self._toMove = "b"
            self._waiting = "w"
        else:
            self._toMove = "w"
            self._waiting = "b"

    def _isPiece(self, itm):
        "Is the itm a piece class?"
        return type(itm) == piece

    def move(self, oldSquare: str, newSquare: str):
        "Execute specified move from old to new"

        movingPiece = self.board[oldSquare]
        potentialMove = {
            "piece": str(movingPiece),
            "oldSquare": oldSquare,
            "newSquare": newSquare,
        }

        # Ensure we are only moving pieces
        if not self._isPiece(itm=movingPiece):
            raise MoveError("Must move a piece")

        # Only move if its your turn
        if movingPiece.color != self._toMove:
            raise MoveError(f"It is {self._toMove} turn")
        print(f"Moving {movingPiece} from {oldSquare}->{newSquare}")

        # Get valid moves, ensure this move is in list
        validMoves = getValidMoves(self.board, self._toMove, self._moves)
        foundMove = None
        for m in validMoves:
            if all(
                [m[k] == potentialMove[k] for k in ["piece", "oldSquare", "newSquare"]]
            ):
                foundMove = m.copy()
                break
        if foundMove is None:
            raise MoveError(f"Invalid move {potentialMove}")

        # Update board, change turn, save move
        self.board = getNewBoard(self.board, foundMove)
        self.board[newSquare].moveCnt += 1
        self._changeTurn()
        self._moves.append(foundMove)

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
    game.move("e2", "e4")
    game.move("f7", "f6")
    game.move("d2", "d4")
    # game.move("g7", "g5")
    # game.move("d1", "h5")
    moves = pd.DataFrame(getValidMoves(game.board, game._toMove, game._moves))
    # game.move("c8", "d7")
    # game.move("e1", "g1")
    # game.move("d7", "f5")
    # game.move("e4", "f5")
    # game.move("d8", "d7")
    # game.move("f3", "d4")
    # game.move("e8", "c8")
    # game.move("e7", "f6")
    # game.move("f1", "c4")

    # game.move("g8", "g6")
    # game.move("e5", "e4")
    # print(game)
    # game.move("c8", "d7")
    print(game)
    # print(game._moves)

# %%
