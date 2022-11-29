# %% Imports
from copy import deepcopy
from typing import List, Literal, Tuple, TypedDict, Union

import numpy as np
import pandas as pd
import plotly.express as px

# import plotly.graph_objects as go
from collections import defaultdict
from helpers import dfToTable, executeSql, getRelativeFp, logger


# %% Logging
log = logger(getRelativeFp(__file__, "logs/chess.log"), 10, 20, True)
# %% Constants
FILES = ["a", "b", "c", "d", "e", "f", "g", "h"]
RANKS = ["1", "2", "3", "4", "5", "6", "7", "8"]
squareType = Literal[
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "a6",
    "a7",
    "a8",
    "b1",
    "b2",
    "b3",
    "b4",
    "b5",
    "b6",
    "b7",
    "b8",
    "c1",
    "c2",
    "c3",
    "c4",
    "c5",
    "c6",
    "c7",
    "c8",
    "d1",
    "d2",
    "d3",
    "d4",
    "d5",
    "d6",
    "d7",
    "d8",
    "e1",
    "e2",
    "e3",
    "e4",
    "e5",
    "e6",
    "e7",
    "e8",
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "g1",
    "g2",
    "g3",
    "g4",
    "g5",
    "g6",
    "g7",
    "g8",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "h7",
    "h8",
]
SQUARES: list[squareType] = [
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "a6",
    "a7",
    "a8",
    "b1",
    "b2",
    "b3",
    "b4",
    "b5",
    "b6",
    "b7",
    "b8",
    "c1",
    "c2",
    "c3",
    "c4",
    "c5",
    "c6",
    "c7",
    "c8",
    "d1",
    "d2",
    "d3",
    "d4",
    "d5",
    "d6",
    "d7",
    "d8",
    "e1",
    "e2",
    "e3",
    "e4",
    "e5",
    "e6",
    "e7",
    "e8",
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "g1",
    "g2",
    "g3",
    "g4",
    "g5",
    "g6",
    "g7",
    "g8",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "h7",
    "h8",
]

PIECENAME = Literal["P", "R", "N", "B", "Q", "K"]
DBPATH = getRelativeFp(__file__, "../data/db/chess.db")

BOARDSCORES: dict[str, int] = {}


# %% Exceptions
class MoveError(Exception):
    "Generic error for move errors"
    pass


class GameError(Exception):
    "Generic error for chess game"
    pass


# %% Objects that go into squares
class empty(object):
    "Empty square of board"

    def __init__(self):
        pass

    def __repr__(self) -> str:
        return "  "


class piece(object):
    "Piece square on board"

    def __init__(self, color, name: PIECENAME, hasMoved=False):
        assert color in ["b", "w"], "Invalid color"
        assert name in ["K", "Q", "B", "N", "R", "P"], "Invalid name"
        self.color: Literal["w", "b"] = color
        self.name: PIECENAME = name
        self.hasMoved: bool = hasMoved
        self.value: int
        if name == "K":
            self.value = 100
        elif name == "Q":
            self.value = 9
        elif name == "R":
            self.value = 5
        elif name == "B":
            self.value = 3
        elif name == "N":
            self.value = 3
        elif name == "P":
            self.value = 1

    def __repr__(self):
        return self.color + self.name


# %%
class attackDictContents(TypedDict):
    w: list[int]
    b: list[int]
    value: int
    pieceColor: str | None


# %% Database encoding functions
class moveDict(TypedDict):
    "Dict of move info"
    piece: str
    oldSquare: str
    newSquare: str
    special: Union[None, str]


class potentialMoveDict(TypedDict):
    "Dict of move info"
    piece: str
    oldSquare: str
    potentialNewSquare: str
    special: Union[None, str]


boardDict = dict[squareType, empty | piece]


# Move encoding to str and back
def move2Str(move: moveDict) -> str:
    "Encodes a move into a str for storage in db"
    out = move["piece"] + move["oldSquare"] + move["newSquare"]
    if move["special"] is None:
        pass
    else:
        out += move["special"]
    return out


def str2Move(s: str) -> moveDict:
    "Parses a str to get a move dict, keys=piece, oldSquare, newSquare, special"
    out: moveDict = {
        "piece": s[:2],
        "oldSquare": s[2:4],
        "newSquare": s[4:6],
        "special": None,
    }
    if len(s) != 6:
        out["special"] = s[6:]
    return out


# Square encoding to str and back
def square2Str(squareObj: empty | piece) -> str:
    "Encodes a square object into a str"
    if isinstance(squareObj, empty):
        return ""
    return squareObj.color + squareObj.name + str(squareObj.hasMoved)[0]


def str2Square(s: str) -> Union[empty, piece]:
    "Parses a str to get a square object (empty or piece)"
    if len(s) == 2:  # If empty square, init empty
        return empty()
    else:  # If there is something
        assert len(s) == 5, "should only be 5 characters for encoding a piece"
        return piece(color=s[2], name=s[3], hasMoved=s[4] == "T")  # type: ignore


# Board encoding to str and back
def board2Str(board: boardDict) -> str:
    "Encodes a board into a string format for storage in db"
    boardStr = " ".join([s + square2Str(board[s]) for s in board])
    return boardStr


def str2Board(s: str) -> boardDict:
    "Parses a string, returning a dict of objects of current game state"
    boardList = s.split()
    assert len(boardList) == 64, boardList
    out: boardDict = {}
    for s in boardList:
        square = s[:2]
        assert square in SQUARES, square
        # assert isinstance(square, squareType), "Not a square"
        out[square] = str2Square(s)  # type: ignore

    return out


# List of moves encoding to str and back
def moves2Str(moves: List[moveDict]) -> str:
    return " ".join([move2Str(m) for m in moves])


def str2Moves(s: str) -> List[moveDict]:
    return [str2Move(m) for m in s.split(" ")]


# List of boards encoding to str and back
def boards2Str(boards: List[dict]) -> str:
    return ",".join([board2Str(b) for b in boards])


def str2Boards(s: str) -> List[dict]:
    if len(s) == 0:
        return []
    return [str2Board(b) for b in s.split(",")]


# %% Getting boards dict from DB
# TODO this is such a big table cause of the strings...how to make smaller?
# def getBoardsDict() -> dict:
#     boards = readSql("select * from boards", DBPATH)
#     boardsDict = {}

#     def addToDict(row):
#         validMoves = str2Moves(row["validMovesStr"])
#         validBoardsList = str2Boards(row["validBoardsStr"])
#         validBoardsDict = {}
#         for move, board in zip(validMoves, validBoardsList):
#             validBoardsDict[move2Str(move)] = board
#         boardsDict[(row["boardStr"], row["toMove"])] = {
#             "validMoves": validMoves,
#             "validBoards": validBoardsDict,
#         }

#     boards.apply(lambda row: addToDict(row), axis=1)

#     return boardsDict


# BOARDSDICT = getBoardsDict()


# %% Todos
# TODO a lot of this is repeated, especially openings. Save in DB?

# %% Functions
def isLastRank(color: Literal["w", "b"], s: squareType) -> bool:
    "Is square s the last rank aka promotion time?"
    return int(s[1]) - [7, 0][color == "b"] == 1


def getKingSquare(board: boardDict, color: Literal["w", "b"]) -> squareType:
    "Returns the square in which the king is located"

    for s in SQUARES:
        if str(board[s]) == color + "K":
            return s

    raise ValueError(f"No king square for {color}")


def getRelativeLoc(color: Literal["w", "b"], loc: squareType, addRank: int, addFile: int) -> squareType:
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

    out: squareType = relFile + relRank
    if out in SQUARES:

        return out

    pass


def getOtherColor(c: Literal["w", "b"]) -> Literal["w", "b"]:
    "Returns the other color of c=w or c=b"
    # assert c in ["w", "b"], f"Invalid color {c}"
    if c == "w":
        return "b"
    return "w"


def getLineFrom(color: Literal["w", "b"], loc: squareType, rankIncrement: int, fileIncrement: int) -> List[squareType]:
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
    out: list[squareType] = [
        getRelativeLoc(color, loc, addRank=(i + 1) * rankIncrement, addFile=(i + 1) * fileIncrement)
        for i in range(7)
        if getRelativeLoc(color, loc, addRank=(i + 1) * rankIncrement, addFile=(i + 1) * fileIncrement) in SQUARES
    ]
    return out


def getKnightAttackSquares(loc: squareType) -> List[squareType]:
    "Returns all the squares that are one knight-jump away from loc"
    out: list[squareType] = [
        getRelativeLoc("w", loc, r * rankMult, f * fileMult)
        for r, f in zip([1, 2], [2, 1])
        for rankMult in [-1, 1]
        for fileMult in [-1, 1]
        if getRelativeLoc("w", loc, r * rankMult, f * fileMult) in SQUARES
    ]
    return out


class attackableSquares(TypedDict):
    straights: list[list[squareType]]
    diagonals: list[list[squareType]]
    knights: list[squareType]
    wP: list[squareType]
    bP: list[squareType]
    kings: list[squareType]


squareDictType = dict[squareType, attackableSquares]


def getSquareDict() -> squareDictType:
    """Get a dict of all the attack squares from every square, based on piece on that square."""
    squareDict: squareDictType = {}
    for square in SQUARES:
        straights = [
            getLineFrom(
                color="w",
                loc=square,
                rankIncrement=i * mult,
                fileIncrement=j * mult,
            )
            for i, j in zip([0, 1], [1, 0])
            for mult in [-1, 1]
        ]
        diagonals = [
            getLineFrom(
                color="w",
                loc=square,
                rankIncrement=i,
                fileIncrement=j,
            )
            for i in [-1, 1]
            for j in [-1, 1]
        ]
        wP = [getLineFrom(color="w", loc=square, rankIncrement=1, fileIncrement=i) for i in [-1, 1]]
        bP = [getLineFrom(color="b", loc=square, rankIncrement=1, fileIncrement=i) for i in [-1, 1]]
        kings = [
            getLineFrom(color="w", loc=square, rankIncrement=i, fileIncrement=j) for i in [-1, 0, 1] for j in [-1, 0, 1]
        ]
        squareDict[square] = {
            "straights": [s for s in straights if len(s) > 0],
            "diagonals": [d for d in diagonals if len(d) > 0],
            "knights": getKnightAttackSquares(square),
            "wP": [s[0] for s in wP if len(s) > 0],
            "bP": [s[0] for s in bP if len(s) > 0],
            "kings": [s[0] for s in kings if len(s) > 0 and s[0] != square],
        }

    return squareDict


SQUAREDICT = getSquareDict()
# log.debug(SQUAREDICT)


# %% More complex functions
def isInCheck(board: boardDict, color: Literal["w", "b"]) -> bool:
    """Given a board layout, returns if specified color is in check

    Args:

        board (dict) -- keys are squares, values are pieces

        color (str) -- w or b

    Returns:

        bool -- is color in check in board?
    """
    global SQUAREDICT

    # Get king square
    otherColor = getOtherColor(color)
    k = getKingSquare(board, color)

    # If a pawn is on a previous rank and adjacent file, return yes
    pawnAttackSquares = [getRelativeLoc(color, k, 1, _) for _ in [1, -1] if getRelativeLoc(color, k, 1, _) in SQUARES]
    for s in pawnAttackSquares:
        if str(board[s]) == otherColor + "P":
            return True

    # Knights being 2,1 or 1,2 +/- on both away means check
    knightAttackSquares = SQUAREDICT[k]["knights"]
    for s in knightAttackSquares:
        if str(board[s]) == otherColor + "N":
            return True

    # Check that closest diagonal piece isn't bishop or Queen or king
    diagonals = SQUAREDICT[k]["diagonals"]
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
    straights = SQUAREDICT[k]["straights"]
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

    # Check that nearest piece in square around given piece isn't other king
    for line in straights + diagonals:
        if len(line) == 0:
            continue
        elif type(line[0]) == empty:
            pass
        elif str(board[line[0]]) == otherColor + "K":
            return True

    return False


def getPotentialValidMoves(board: boardDict, currSquare: squareType, prevMoves: List[moveDict]) -> List[moveDict]:
    """Returns all moves for a piece REGARDLESS of if they leave the moving color in check

    Args:

        board (dict) -- current board with keys=squares, values=pieces or empty

        currSquare (str) -- square from which to get valid moves

        prevMoves (list of dict) -- previous moves in game to-date (for enpassant)

    Returns:

        list of dict -- all moves where piece can end up. Note this list may include some
            where the moving color is in check. dicts have keys 'piece', 'oldSquare', 'newSquare', 'special'
    """

    global SQUAREDICT
    movingPiece = board[currSquare]
    if isinstance(movingPiece, empty):
        return []
    movingColor = movingPiece.color
    diagonals = SQUAREDICT[currSquare]["diagonals"]
    straights = SQUAREDICT[currSquare]["straights"]
    move = {"piece": str(movingPiece), "oldSquare": currSquare, "special": None}

    # King squares
    potentialValidMoves = []
    if movingPiece.name == "K":
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                newLoc = getRelativeLoc(color=movingColor, loc=currSquare, addRank=i, addFile=j)
                if newLoc not in SQUARES:
                    continue
                if newLoc == currSquare:
                    continue
                if str(board[newLoc])[0] == movingColor:
                    continue
                potentialValidMoves.append({**move, "newSquare": newLoc})

        # Short castling - if h-file rook has 0 moves, king has 0 moves, squares between are empty
        if movingPiece.hasMoved:
            pass

        elif str(board[getRelativeLoc("w", currSquare, 0, 3)]) != movingColor + "R":
            pass
        elif board[getRelativeLoc("w", currSquare, 0, 3)].hasMoved:
            pass
        elif type(board[getRelativeLoc("w", currSquare, 0, 1)]) == piece:
            pass
        elif type(board[getRelativeLoc("w", currSquare, 0, 2)]) == piece:
            pass
        elif isInCheck(board, movingColor):
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
        if movingPiece.hasMoved:
            pass
        elif str(board[getRelativeLoc("w", currSquare, 0, -4)]) != movingColor + "R":
            pass
        elif board[getRelativeLoc("w", currSquare, 0, -4)].hasMoved:
            pass
        elif type(board[getRelativeLoc("w", currSquare, 0, -1)]) == piece:
            pass
        elif type(board[getRelativeLoc("w", currSquare, 0, -2)]) == piece:
            pass
        elif type(board[getRelativeLoc("w", currSquare, 0, -3)]) == piece:
            pass
        elif isInCheck(board, movingColor):
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
        for s in SQUAREDICT[currSquare]["knights"]:
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
            # If one ahead is last rank, add promotions only
            if isLastRank(movingColor, oneAhead):
                potentialValidMoves.append({**move, "newSquare": oneAhead, "special": "promoteQ"})
                potentialValidMoves.append({**move, "newSquare": oneAhead, "special": "promoteR"})
                potentialValidMoves.append({**move, "newSquare": oneAhead, "special": "promoteN"})
                potentialValidMoves.append({**move, "newSquare": oneAhead, "special": "promoteB"})
            # If one ahead is not last rank, add pawn move
            else:
                potentialValidMoves.append({**move, "newSquare": oneAhead})
                # If piece move count == 0 then two ahead is allowed if its not a piece
                twoAhead = getRelativeLoc(movingColor, currSquare, 2, 0)
                if not movingPiece.hasMoved:
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
                    # If take is last rank only add promotions
                    if isLastRank(movingColor, takeSquare):
                        potentialValidMoves.append({**move, "newSquare": takeSquare, "special": "promoteQ"})
                        potentialValidMoves.append({**move, "newSquare": takeSquare, "special": "promoteR"})
                        potentialValidMoves.append({**move, "newSquare": takeSquare, "special": "promoteN"})
                        potentialValidMoves.append({**move, "newSquare": takeSquare, "special": "promoteB"})
                    # If take is not last rank add normal take
                    else:
                        potentialValidMoves.append({**move, "newSquare": takeSquare})

        # en passant logic
        # If prevmove was two squares forward and one square back was takeable is square in takeSquares?
        if len(prevMoves) == 0:  # first move can't be en passant
            pass
        else:
            prevMove = prevMoves[-1]
            otherColor = getOtherColor(movingColor)
            prevMoveOneSquareBack = getRelativeLoc(otherColor, prevMove["newSquare"], -1, 0)
            if prevMove["piece"] != otherColor + "P":  # If prevmove not pawn
                pass
            elif abs(int(prevMove["newSquare"][1]) - int(prevMove["oldSquare"][1])) != 2:  # prevmove wasnt two squares
                pass
            elif prevMoveOneSquareBack not in takeSquares:  # Wasn't take opp
                pass
            else:
                potentialValidMoves.append({**move, "newSquare": prevMoveOneSquareBack, "special": "enpassant"})

    return potentialValidMoves


def getNewBoard(board: dict, move: dict) -> dict:
    """Returns what the new board would look like after move is executed.
    Handles pawn promotions, long and short castles, and enpassant

    Args:

        board (dict) -- keys are squares, values are pieces

        move (dict) -- piece, oldSquare, newSquare, special

    Returns:

        dict -- updated board after executing move
    """

    # Ensure move matches pattern
    if sorted(move.keys()) != ["newSquare", "oldSquare", "piece", "special"]:
        raise MoveError("Specified move does not have all required elements")

    newBoard = board.copy()
    movingPiece = deepcopy(board[move["oldSquare"]])
    movingPiece.hasMoved = True
    movingColor = movingPiece.color

    if move["piece"] != str(movingPiece):
        raise MoveError(f"Square {move['oldSquare']} does not have piece {move['piece']}")
    newBoard[move["newSquare"]] = movingPiece
    newBoard[move["oldSquare"]] = empty()

    # Promotion Logic - create new piece in location
    if move["special"] in [f"promote{p}" for p in ["Q", "N", "R", "B"]]:
        newBoard[move["newSquare"]] = piece(movingColor, move["special"][-1], hasMoved=True)

    if move["special"] == "enpassant":
        newBoard[getRelativeLoc(movingColor, move["newSquare"], -1, 0)] = empty()
    if move["special"] == "shortCastle":
        newBoard[getRelativeLoc("w", move["newSquare"], 0, -1)] = deepcopy(
            newBoard[getRelativeLoc("w", move["newSquare"], 0, 1)]
        )
        newBoard[getRelativeLoc("w", move["newSquare"], 0, -1)].hasMoved = True
        newBoard[getRelativeLoc("w", move["newSquare"], 0, 1)] = empty()
    if move["special"] == "longCastle":
        newBoard[getRelativeLoc("w", move["newSquare"], 0, 1)] = deepcopy(
            newBoard[getRelativeLoc("w", move["newSquare"], 0, -2)]
        )
        newBoard[getRelativeLoc("w", move["newSquare"], 0, 1)].hasMoved = True
        newBoard[getRelativeLoc("w", move["newSquare"], 0, -2)] = empty()

    return newBoard


def getValidMoves(
    board: boardDict, color: Literal["w", "b"], prevMoves: List[moveDict]
) -> Tuple[list[moveDict], dict[str, boardDict]]:
    """Gets all valid moves for a specific color. If list length = 0, checkmate!

    Args:

        board (dict) -- keys are squares, values are pieces

        color (str) -- w or b

        prevMoves (list of dict) -- previous moves in game to-date (for enpassant)

    Returns:

        tuple of list, dict -- list of valid moves with keys piece, oldSquare, newSquare, special
            and dict of boards after executing said move. Key for the dict is str(move)

    """

    potentialValidMoves = []
    validMoves = []
    validBoards = {}

    # Loop through squares, if square has same-color piece, save potential valid moves
    for currSquare in board:
        if type(board[currSquare]) == empty:
            continue

        movingPiece = board[currSquare]
        if str(movingPiece)[0] != color:
            continue

        potentialValidMoves += getPotentialValidMoves(board, currSquare, prevMoves)
    # See if potential move results in check, if not, save move and board
    for move in potentialValidMoves:
        newBoard = getNewBoard(board, move)
        if isInCheck(newBoard, color):
            continue

        validMoves.append(move)
        validBoards[move2Str(move)] = newBoard

    return validMoves, validBoards


# %% Score board
# @log.timeFuncInfo
def getScore(board: boardDict, toMove: Literal["w", "b"], prevMoves: list[moveDict]) -> tuple[pd.DataFrame, int]:
    """Gets score of a board. Returns everything where the perspective of 'toMove' is positive.

    E.g.:
    """

    # TODO how to handle split attacks (e.g. knight shouldn't get both)
    scores = pd.DataFrame(index=[x for x in reversed(RANKS)], columns=FILES, data=0)
    # boardWithColor = f"{getOtherColor(toMove)} | {board2Str(board)}"
    log.debug(f"toMove: {toMove}")
    # For any opponent color piece with >1 attack on it:
    # Value for me = +(value of piece under attack)
    #   - (value of n lowest pieces attacking it for n number defending)
    #  + (value of m lowest pieces defending it for m-1 number attacking)

    # Example, N attacking Q defended by P
    #   +9 - [3] + 0 = +6

    # Example NPB attacking P defended by NP
    #  +1 - [1, 3] + [3 + 1] = +1

    # Handle checks - if is in check, only allow moves that get out of check
    if isInCheck(board, toMove):
        validMoves = getValidMoves(board, toMove, prevMoves)[0]
        log.debug(f"{toMove} is in check, only considering {len(validMoves)} valid moves")
        if len(validMoves) == 0:
            for col in scores.columns:
                scores[col] = 10
            return scores, 1000

    attackDict: dict[squareType, attackDictContents] = defaultdict(
        lambda: {"w": [], "b": [], "value": 0, "pieceColor": None}
    )
    pieceValuesOnBoard = {"w": 0, "b": 0}
    for square, p in board.items():
        if isinstance(p, empty):
            continue
        pieceValuesOnBoard[p.color] += p.value
        attackDict[square]["value"] = p.value
        attackDict[square]["pieceColor"] = p.color
        if p.name == "P":
            for sq in SQUAREDICT[square][str(p)]:
                attackDict[sq][p.color].append(p.value)
        elif p.name == "N":
            for sq in SQUAREDICT[square]["knights"]:
                attackDict[sq][p.color].append(p.value)

        elif p.name == "B":
            for line in SQUAREDICT[square]["diagonals"]:
                for sq in line:
                    attackDict[sq][p.color].append(p.value)
                    if isinstance(board[sq], type(p)):
                        break
        elif p.name == "R":
            for line in SQUAREDICT[square]["straights"]:
                for sq in line:
                    attackDict[sq][p.color].append(p.value)
                    if isinstance(board[sq], type(p)):
                        break
        elif p.name == "Q":
            for line in SQUAREDICT[square]["diagonals"] + SQUAREDICT[square]["straights"]:
                for sq in line:
                    attackDict[sq][p.color].append(p.value)
                    if isinstance(board[sq], type(p)):
                        break
        elif p.name == "K":
            for sq in SQUAREDICT[square]["kings"]:
                attackDict[sq][p.color].append(p.value)

    for square, stuff in attackDict.items():
        if stuff["value"] == 0:
            continue
        if (len(stuff["w"]) == 0) & (len(stuff["b"]) == 0):
            continue
        if stuff["pieceColor"] == toMove:
            continue
        attacks = sorted(stuff[toMove])
        defends = sorted(stuff[getOtherColor(toMove)])
        attackCnt = len(attacks)
        defendCnt = len(defends)
        if attackCnt == 0:
            continue
        log.debug(f"{square}, {stuff}")
        log.debug(f"attacks: {attacks}, defends: {defends}")
        nv = stuff["value"] - sum(attacks[:defendCnt]) + sum(defends[: attackCnt - 1])
        log.debug(f"nv: {nv}")
        if (nv > 0) or (defendCnt == 0):
            scores[square[0]][square[1]] += stuff["value"]
            log.debug(f"{square} value {stuff['value']} attacks: {attacks}, defends: {defends}, net: {nv}")

    log.debug(pieceValuesOnBoard)

    boardVal = pieceValuesOnBoard[toMove] - pieceValuesOnBoard[getOtherColor(toMove)]

    return scores, boardVal


# %% Chess game class
class chessGame(object):
    "High-level object to store chess game state"

    def __init__(self):
        # Create chess board, load up pieces
        self.board: boardDict = {}
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
        self.toMove: Literal["w", "b"] = "w"
        self.waiting: Literal["w", "b"] = "b"
        self.prevMoves: list[moveDict] = []
        self.validMoves, self.validBoards = getValidMoves(self.board, self.toMove, self.prevMoves)
        self.winner = None

    def _changeTurn(self):
        if self.toMove == "w":
            self.toMove = "b"
            self.waiting = "w"
        else:
            self.toMove = "w"
            self.waiting = "b"

    def move(self, oldSquare: str, newSquare: str, promoteTo: Union[str, None] = None):
        "Execute specified move from old to new"

        movingPiece = self.board[oldSquare]
        potentialMove = {
            "piece": str(movingPiece),
            "oldSquare": oldSquare,
            "newSquare": newSquare,
            "special": None,
        }

        if promoteTo is not None:
            potentialMove["special"] = f"promote{promoteTo}"

        # Ensure the game is not over
        if self.winner is not None:
            raise MoveError(f"Game is over, {self.winner} already won!")

        # Ensure we are only moving pieces
        if not isinstance(movingPiece, piece):
            raise MoveError("Must move a piece")

        # Only move if its your turn
        if movingPiece.color != self.toMove:
            raise MoveError(f"It is {self.toMove} turn")

        # Get valid moves, ensure this move is in list
        foundMoves = []
        for m in self.validMoves:
            if all([m[k] == potentialMove[k] for k in ["piece", "oldSquare", "newSquare"]]):
                foundMoves.append(m.copy())
        if len(foundMoves) == 0:
            raise MoveError(f"Invalid move {potentialMove}")
        elif len(foundMoves) >= 2:
            foundMoves = [m for m in foundMoves if (m["special"] == f"promote{promoteTo}")]
            if len(foundMoves) != 1:
                raise MoveError(f"Found too many moves {foundMoves}")

        foundMove = foundMoves[0]

        # Update board, change turn, save move, get next player's valid moves
        self.board = self.validBoards[move2Str(foundMove)]
        self._changeTurn()
        self.prevMoves.append(foundMove)
        self.board[newSquare].hasMoved = True
        self.validMoves, self.validBoards = getValidMoves(self.board, self.toMove, self.prevMoves)

        # Handle winning scenario
        if len(self.validMoves) == 0:
            self.winner = getOtherColor(self.toMove)

    def show(self):
        scores, boardVal = getScore(self.board, self.toMove, self.prevMoves)
        fig = px.imshow(scores.values, x=FILES, y=[x for x in reversed(RANKS)])
        for x in range(7):
            fig.add_hline(x + 0.5, line_width=1, line_color="black")
            fig.add_vline(x + 0.5, line_width=1, line_color="black")
        for square, piece in self.board.items():
            if isinstance(piece, empty):
                continue
            sqIdx = (FILES.index(square[0]), RANKS.index(square[1]))

            fig.add_layout_image(
                row=1,
                col=1,
                source=getRelativeFp(__file__, f"../{piece}.png"),
                xref="x domain",
                yref="y domain",
                x=(sqIdx[0] + 1) / 8,
                y=((sqIdx[1] + 1) / 8),
                xanchor="right",
                yanchor="top",
                sizex=0.125,
                sizey=0.125,
            )

        netScore = (boardVal + scores.values.sum()) * ([-1, 1][self.toMove == "w"])
        # netScore *= 1 if self.toMove == "w" else -1
        fig.update_layout(
            title_text=f"Score: {netScore}, To move: {self.toMove}, Waiting: {self.waiting}, Winner: {self.winner}",
        )
        fig.show()

    def recMove(self, depth=2):
        "Recommend a move. All scores are in"

        # Get valid moves, ensure there are some
        if len(self.validMoves) == 0:
            raise MoveError("No valid moves")

        # Get best move
        for move, board in zip(self.validMoves, self.validBoards.values()):
            boardWithColor = f"{getOtherColor(self.toMove)} | {board2Str(board)}"
            try:
                netScore = BOARDSCORES[boardWithColor]
            except KeyError:
                log.debug(board2Str(board))
                scores, boardVal = getScore(board, getOtherColor(self.toMove), self.prevMoves)
                netScore = boardVal + scores.values.sum()
                netScore = boardVal + scores.values.sum()  # * ([-1, 1][self.toMove == "w"])
                BOARDSCORES[boardWithColor] = netScore
            log.info(
                f"From {self.toMove} persp: {move2Str(move)} results in {getOtherColor(self.toMove)} score of {netScore}"
            )
            # log.info(netScore)
            # if there is a M1 (board value > 100), return that move
            if netScore > 100:
                return move


# %% Transcribe game into engine
def findMove(move: pd.Series, validMoves: List[dict]):
    """Gets the specified move dict from list of validMoves.

    Args:

        move (Series) -- a row from moveDf, with values for:
            color, piece, oldFile, oldRank, take, newSquare, promoteTo, check, mate, special

        validMoves (list of dict) -- a list of valid moves given board state. Dict keys are:
            piece, oldSquare, newSquare, special
    """

    # Look for validmoves that match piece and newsquare
    matches = []
    for validMove in validMoves:
        if all([move[f] == validMove[f] for f in ["piece", "newSquare"]]):
            matches.append(validMove)

    # If move is promotion, filter to the validmoves where promotion matches
    if type(move["promoteTo"]) == str:
        matches = [m for m in matches if m["special"] == f"promote{move['promoteTo']}"]

    # If exactly one matching move found, return that
    if len(matches) == 1:
        return matches[0]

    # If more than one match
    elif len(matches) > 1:

        # Handle pawn and rook takes with multiple options
        # (if notation specifies file OR rank)
        matches = [
            m for m in matches if (m["oldSquare"][0] == move["oldFile"]) | (m["oldSquare"][1] == move["oldRank"])
        ]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            raise MoveError(f"No matches after looking for matching rank or file")

        else:  # If we have more than 1 match still
            # Look for matching rank AND file
            matches = [m for m in matches if (m["oldSquare"] == move["oldFile"] + move["oldRank"])]
            if len(matches) == 1:
                return matches[0]
            elif len(matches) == 0:
                raise MoveError(f"No matches after looking for matching rank and/or file")

            else:
                raise MoveError(f"More than one match found for {move['move']}")
    else:
        raise MoveError(f"No matching move for {move['move']}")


def movesStrIntoDf(movesStr: str) -> pd.DataFrame:
    """Takes a move str and returns a parsed DataFrame of all the moves.

    Args:

        movesStr (str) -- chess notation of all the game's moves

    Returns:

        DataFrame -- columns are:
            move (original string in chess notation),
            color (w or b),
            piece (P, R, N, B, Q, K),
            oldFile (for identifying rook/pawn/knight takes),
            oldRank (for identifying rook/pawn/knight takes),
            take (x if move was take),
            newSquare (where old piece ended up),
            promoteTo (piece pawn was promoted to, QNRB),
            check (+ if move results in opp in check),
            mate (# if move results in opp in mate),
            special (longCastle, shortCastle, promote<promoteTo>)
    """
    moves = movesStr.split(" ")
    moveDf = pd.DataFrame({"move": moves, "color": np.tile(["w", "b"], len(moves))[: len(moves)]})
    moveDf[["piece", "oldFile", "oldRank", "take", "newSquare", "promoteTo", "check", "mate",]] = moveDf[
        "move"
    ].str.extract(r"([RBNKQ]{1})?([a-h])?([0-8])?(x)?([a-h][0-8])=?([RBNQ])?(\+)?(\#)?")

    # Handle castle notation
    moveDf.loc[moveDf["move"].str[:3] == "O-O", "piece"] = "K"
    moveDf.loc[(moveDf["move"].str[:3] == "O-O") & (moveDf["color"] == "w"), "newSquare"] = "g1"
    moveDf.loc[(moveDf["move"].str[:3] == "O-O") & (moveDf["color"] == "b"), "newSquare"] = "g8"
    moveDf.loc[(moveDf["move"].str[:5] == "O-O-O") & (moveDf["color"] == "w"), "newSquare"] = "c1"
    moveDf.loc[(moveDf["move"].str[:5] == "O-O-O") & (moveDf["color"] == "b"), "newSquare"] = "c8"

    # Get piece name
    moveDf["piece"] = moveDf["color"] + moveDf["piece"].fillna("P")

    # Fill special with contents
    moveDf["special"] = None
    moveDf.loc[moveDf["move"].str[:3] == "O-O", "special"] = "shortCastle"
    moveDf.loc[moveDf["move"].str[:5] == "O-O-O", "special"] = "longCastle"
    moveDf.loc[moveDf["promoteTo"] == "Q", "special"] = "promoteQ"
    moveDf.loc[moveDf["promoteTo"] == "R", "special"] = "promoteR"
    moveDf.loc[moveDf["promoteTo"] == "N", "special"] = "promoteN"
    moveDf.loc[moveDf["promoteTo"] == "B", "special"] = "promoteB"

    return moveDf


def parseGameRow(gameRow: pd.Series, updateEvery: int = 50):
    if gameRow.name % updateEvery == 0:
        log.info(f"On game {gameRow.name}")

    moveDf = movesStrIntoDf(gameRow["moves"])

    moveNums = []
    oldBoardStr = []
    moveStr = []
    newBoardStr = []
    # Create game, iterate through moves
    game = chessGame()
    for idx, move in moveDf.iterrows():
        moveNums.append(idx + 1)
        oldBoardStr.append(board2Str(game.board))
        validMoves = game.validMoves
        validMove = findMove(move, validMoves)
        if validMove["special"] in [f"promote{p}" for p in ["Q", "R", "N", "B"]]:
            promoteTo = validMove["special"][-1]
        else:
            promoteTo = None

        moveStr.append(move2Str(validMove))
        game.move(validMove["oldSquare"], validMove["newSquare"], promoteTo)
        newBoardStr.append(board2Str(game.board))

    # If outcome is mate, ensure it matches the results of my engine
    if type(gameRow["mateColor"]) == str:
        if type(game.winner) == str:
            if game.winner != gameRow["mateColor"]:
                log.info(game)
                raise GameError(f"Engine has winner as {game.winner}, data has {gameRow['mateColor']}")
    else:
        # log.info(f"Finished entirety of moves with no outcome")
        pass

    out = pd.DataFrame(
        {
            "gameId": [gameRow["id"]] * len(moveDf),
            "moveNum": moveNums,
            "oldBoardStr": oldBoardStr,
            "moveStr": moveStr,
            "newBoardStr": newBoardStr,
        }
    )
    dfToTable(out, "moves", DBPATH, ifExists="append", indexCols=None)
    executeSql(
        f"""
        Insert into games values (
            '{gameRow['id']}',
            '{gameRow['rated'] == 'true'}',
            '{gameRow['turns']}',
            '{gameRow['winner'][0]}',
            '{gameRow['victory_status']}',
            '{gameRow['increment_code']}',
            '{gameRow['white_rating']}',
            '{gameRow['black_rating']}',
            '{gameRow['moves']}'
        )
        """,
        DBPATH,
    )


# Database table creation
def createBoardsTable(dbPath, dropOld=False):
    """
    Creates table 'boards', mapping moves to board layout.

    Columns:
        boardStr: string of board layout
        toMove: str of color to move
        validMovesStr: str of list of valid moves
        validBoardsStr: str of list of validBoards, comma separated

    Index on boardStr, toMove.

    Passes through all commands to runSqlQuery fn,
    so if default args for that change, so will this.

    """
    # Drop old table if exists
    if dropOld:
        q = f"""
        drop table if exists boards
        """
        executeSql(q, dbPath)

    # Create table and indeces
    q = f"""
    create table boards(
        boardStr TEXT not null,
        toMove TEXT not null,
        validMovesStr TEXT,
        validBoardsStr TEXT,
        primary key (boardStr asc, toMove asc)
    )
    """
    executeSql(q, dbPath)
    q = f"""
    CREATE INDEX boardsBoardStrToMoveIdx
    ON boards(boardStr, toMove)
    """
    log.info(f"Success!")


def createMovesTable(dbPath, dropOld=False):
    # Drop old table if exists
    if dropOld:
        q = f"""
        drop table if exists moves
        """
        executeSql(q, dbPath)

    # Create table and indeces
    q = f"""
    create table moves(
        gameId TEXT not null,
        moveNum INTEGER not null,
        oldBoardStr TEXT not null,
        moveStr TEXT not null,
        newBoardStr TEXT not null,
        primary key (gameId asc, moveNum asc)
    )
    """
    executeSql(q, dbPath)
    q = f"""
    CREATE INDEX movesIndex
    ON moves(gameId, moveNum)
    """
    log.info(f"Success!")


def createGamesTable(dbPath, dropOld=True):
    # Drop old table if exists
    if dropOld:
        q = f"""
        drop table if exists games
        """
        executeSql(q, dbPath)

    # Create table and indeces
    q = f"""
    create table games(
        gameId TEXT not null,
        isRated integer not null,
        turnCount integer not null,
        winner text not null,
        winCondition text not null,
        increment text not null,
        whiteRating integer not null,
        blackRating integer not null,
        movesStr TEXT not null,
        primary key (gameId asc)

    )
    """
    executeSql(q, dbPath)
    q = """
    CREATE INDEX gamesIndex
    ON moves(gameId)
    """
    log.info("Success!")


# %% Main
if __name__ == "__main__":
    # Simple M1 blunders abound
    # game = chessGame()
    # game.move("f2", "f3")
    # game.move("e7", "e5")
    # game.move("g2", "g4")
    # print(game.recMove())
    # game.show()

    # Other game
    game = chessGame()
    game.move("e2", "e4")
    game.move("e7", "e5")
    game.move("g1", "f3")
    game.move("b8", "c6")
    game.move("f1", "c4")
    game.move("g8", "f6")
    game.move("f3", "g5")
    game.move("d7", "d5")
    game.move("e4", "d5")
    game.move("f6", "d5")
    game.move("g5", "f7")
    game.move("e8", "f7")
    game.move("d1", "g4")
    game.recMove()
    game.show()
    # game.move("d5", "f4")

    # game.move("e4", "d3")
    # moves = pd.DataFrame(game.validMoves)
    # game.move("h7", "g8", "Q")
    # game.move("a7", "a6")
    # game.move("d1", "f3")
    # game.move("a6", "a5")
    # game.move("f3", "f7")
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
    # log.info(game)
    # game.move("c8", "d7")
    # log.info(game)
    # log.info(game.prevMoves)

# %%
