from functools import reduce

import pandas as pd

from hedge_it.commons import get_logger
from hedge_it.commons.constants import (
    CLOSE,
    DATE,
    HIGH,
    LOW,
    M_CAP,
    OPEN,
    SHARES,
    TICKER,
    VOLUME,
)

log = get_logger()


def process_ticker_data(ticker_stocks: pd.DataFrame) -> pd.DataFrame:
    cols = [OPEN, CLOSE, LOW, HIGH, VOLUME]
    melted_dfs = []
    for col in cols:
        melted_df = (
            ticker_stocks[col]
            .reset_index()
            .melt(id_vars=[DATE], var_name=TICKER, value_name=col)
            .reset_index(drop=True)
        )
        melted_dfs.append(melted_df)
    ticker_df = reduce(
        lambda left, right: pd.merge(left, right, on=[DATE, TICKER]), melted_dfs
    )
    log.info(f"Ticker Data Processed: {ticker_df.shape}")
    return ticker_df


def compute_market_cap(
    ticker_history: pd.DataFrame, ticker_shares_history: pd.DataFrame
) -> pd.DataFrame:
    log.info(
        f"Computing Market Cap.TickerShares({ticker_history.shape}) and TickerHistory({ticker_shares_history.shape}).",
    )
    stocks_df = pd.merge(
        ticker_shares_history, ticker_history, on=[TICKER], how="inner"
    )
    stocks_df[M_CAP] = stocks_df[SHARES] * stocks_df[CLOSE]
    log.info("Market Cap Computed.")
    return stocks_df


def ticker_processor(
    ticker_stocks: pd.DataFrame, ticker_shares: pd.DataFrame
) -> pd.DataFrame:
    log.info(
        "Processing Ticker Data and Computing Market Cap.",
    )
    ticker_df = process_ticker_data(ticker_stocks)
    stocks_df = compute_market_cap(ticker_df, ticker_shares)
    log.info(f"ticker_processor Completed. Stocks DataFrame: {stocks_df.shape}")
    return stocks_df
