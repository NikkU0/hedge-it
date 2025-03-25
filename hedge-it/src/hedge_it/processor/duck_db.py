import duckdb
import pandas as pd

from hedge_it.commons import get_logger
from hedge_it.commons.constants import STOCKS, TABLE_TOPM
from hedge_it.processor.queries import (
    equal_weighted_index_builder,
    equal_weighted_index_query,
    get_index_stock_composition,
    topn_mcap_query,
)

log = get_logger()


def duckconn(db: str = STOCKS):
    return duckdb.connect(f"{db}.duckdb")


def persist_stock_df(stock_df: pd.DataFrame, table_name: str = STOCKS):
    conn = duckconn()
    conn.register("stocks", stock_df)

    table_exists_query = f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_name}'"
    table_exists = conn.execute(table_exists_query).fetchone()[0] > 0
    if table_exists:
        query = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM stocks"
    else:
        query = f"CREATE TABLE {table_name} AS SELECT * FROM stocks"

    log.info(f"Stocks Query: {query}")
    conn.execute(query)


def persist_top_mcap(top_n: int, stock_table_name: str = STOCKS):
    query = topn_mcap_query(top_n=top_n, stock_table_name=stock_table_name)
    conn = duckconn()
    table_exists_query = f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{TABLE_TOPM}'"
    table_exists = conn.execute(table_exists_query).fetchone()[0] > 0
    if table_exists:
        query = f"CREATE OR REPLACE TABLE {TABLE_TOPM} AS {query}"
    else:
        query = f"CREATE TABLE {TABLE_TOPM} AS {query}"
    log.info(f"TopMcap Query: {query}")
    conn.execute(query)


def persist_index_table(table_name: str = TABLE_TOPM) -> pd.DataFrame:
    query = (
        f"CREATE OR REPLACE TABLE index AS {equal_weighted_index_builder(table_name)}"
    )
    log.info(f"Index Table Create: {query}")
    duckconn().execute(query)


def query_equal_weighted_index() -> pd.DataFrame:
    query = equal_weighted_index_query()
    log.info(f"Equal Weighted Index Query: {query}")
    return duckconn().execute(query).fetch_df()


def get_stock_composition() -> pd.DataFrame:
    return duckconn().execute(get_index_stock_composition()).fetch_df()
