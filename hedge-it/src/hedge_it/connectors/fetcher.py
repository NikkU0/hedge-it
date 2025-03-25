import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from polygon import ReferenceClient

from hedge_it.commons import get_logger
from hedge_it.commons.constants import DISPLAY_NAME, SHARES, TICKER

from .ticker_history import (
    fetch_ticker_history,
    ticker_by_exchange,
    ticker_outstanding_shares,
)

log = get_logger()


def fetch_stocks(
    polygon_key: str,
    exchanges: list = ["XNYS"],
    stock_limit: int = 200,
    chunk_size: int = 50,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch Tickers from Polygon API. Free Polygon has limit of 5 calls per minute.
    Fetch stock history & outstanding share info from Yahoo Finance API.
    Yahoo Finance API has a limit of 2,000 calls per hour(not sure), IP based.
    """

    def process_results(results: list[dict]) -> pd.DataFrame:
        """Helper function to process and concatenate results."""
        non_empty_results = [result for result in results if result]
        if non_empty_results:
            df = pd.DataFrame(non_empty_results)
            return df.dropna(subset=[TICKER, DISPLAY_NAME, SHARES])
        else:
            log.error("No valid data to concat stocks.")
            return pd.DataFrame()

    poly_ref_client = ReferenceClient(api_key=polygon_key)
    tickers = ticker_by_exchange(poly_ref_client, *exchanges)
    ticker_names = [t["ticker"] for t in tickers[:stock_limit]]

    with ThreadPoolExecutor(max_workers=os.cpu_count() * 10) as executor:
        res_shares = executor.map(ticker_outstanding_shares, ticker_names)

    ticker_shares = process_results(res_shares)

    ticker_stocks = fetch_ticker_history(ticker_shares[TICKER].unique().tolist())
    log.info(
        f"fetch_stocks Completed. Stocks: {ticker_stocks.shape}, Shares: {ticker_shares.shape}"
    )
    return ticker_stocks, ticker_shares
