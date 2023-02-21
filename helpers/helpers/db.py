import pandas as pd
import sqlite3 as sq
from typing import Union, List


def readSql(q: str, db: str) -> pd.DataFrame:
    """Executes query and returns dataframe of results.

    Args:

        q (str) -- query to execute

        db (str) -- path to database on which to run query

    Returns:

        DataFrame -- Results from query
    """
    with sq.connect(db) as con:
        df = pd.read_sql(q, con)

    return df


def executeSql(q: str, db: str) -> None:
    """Runs specified query against database, returning nothing. Use for 'drop table'-like commands.

    Args:

        q (str) -- Query to execute

        db (str) -- path to database on which to run query

    Returns nothing.
    """
    with sq.connect(db) as con:
        cur = con.cursor()
        cur.execute(q)
        con.commit()


def dfToTable(
    df: pd.DataFrame,
    table: str,
    db: str,
    ifExists: str = "replace",
    indexCols: Union[List[str], None] = None,
) -> None:
    """Saves dataframe as table in sqlite3 database

    Args:

        df (pd.DataFrame) -- data to save

        table (str) -- table name

        db (str) -- path to database on which to run query

        ifExists (str) -- pass-thru for pandas arg. "replace" (default), "append", "fail"

        indexCols (list of str) -- cols to be used as index. Defaults to None (no index).

    Returns nothing.
    """

    # Handle dtypes
    df = df.convert_dtypes()

    assert ifExists in ["replace", "append", "fail"], f"Invalid ifExists: {ifExists}"

    # Handle index var
    if indexCols is not None:
        index_label = indexCols
        df.set_index(indexCols, drop=True, inplace=True, verify_integrity=True)
        index = True
    else:
        index_label = None
        index = False

    # Load table
    with sq.connect(db) as con:
        df.to_sql(
            name=table,
            con=con,
            if_exists=ifExists,
            method="multi",
            index=index,
            index_label=index_label,
            chunksize=1000,
        )


def getGroupbyStr(key: List[str]) -> str:
    "Transforms list into comma-separated str (no comma at end)"
    assert type(key) == list, "Please pass list"
    return str(key).replace("'", "")[1:-1]
