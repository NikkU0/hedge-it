from hedge_it.commons.constants import (
    CLOSE,
    DATE,
    DISPLAY_NAME,
    EQUAL_WEIGHTED_INDEX,
    M_CAP,
    SECTOR,
    STOCK_COUNT,
    STOCKS,
    TABLE_TOPM,
    TICKER,
    VALUE,
)


def topn_mcap_query(top_n: int, stock_table_name: str = STOCKS) -> str:
    return f"""
SELECT
  {DATE},
  {TICKER},
  {DISPLAY_NAME},
  {SECTOR},
  {M_CAP},
  {CLOSE}
FROM
  {stock_table_name}
WHERE
  {DATE} >= CURRENT_DATE - INTERVAL 30 DAY
QUALIFY
  ROW_NUMBER() OVER (PARTITION BY {DATE} ORDER BY {M_CAP} DESC) <= {top_n}
ORDER BY
  {DATE},
  {M_CAP} DESC;
"""


def create_topm_table_ddl(mcap_table_name: str = TABLE_TOPM) -> str:
    return f"""CREATE TABLE IF NOT EXISTS {mcap_table_name}"""


def equal_weighted_index_builder(table_name: str) -> str:
    return f"""
WITH
  StockWeights AS (
  SELECT
    {DATE},
    {CLOSE},
    COUNT(*) OVER (PARTITION BY {DATE}) AS {STOCK_COUNT}
  FROM
    {table_name} )
SELECT
  {DATE},
  {STOCK_COUNT},
  SUM({CLOSE} / {STOCK_COUNT}) AS {EQUAL_WEIGHTED_INDEX}
FROM
  StockWeights
GROUP BY
  {DATE}, {STOCK_COUNT}
ORDER BY
  {DATE};
"""


def equal_weighted_index_query() -> str:
    return """SELECT * FROM index;"""


def get_index_stock_composition() -> str:
    return f"""
SELECT *, {CLOSE} / {STOCK_COUNT} AS {VALUE}, {DISPLAY_NAME}
FROM {TABLE_TOPM}
LEFT JOIN index
ON {TABLE_TOPM}.DATE = index.DATE
"""
