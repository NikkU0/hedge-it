import pandas as pd
import yfinance as yf

from hedge_it.commons import get_logger
from hedge_it.commons.constants import (
    CS,
    DISPLAY_NAME,
    INDUSTRY,
    SECTOR,
    SHARES,
    TICKER,
)

from .session import session

log = get_logger()


def ticker_by_exchange(poly_ref_client, *exchanges):
    tickers = []
    api_call_count = 0
    for exchange in exchanges:
        log.info(f"Getting tickers for exchange {exchange}")
        url = None
        while True:
            api_call_count += 1
            if api_call_count > 5:
                log.info(
                    f"Warning: API call count has exceeded 5 Free Polygon has limit of 5 Calls Per Minute. Current count: {api_call_count}"
                )

            response = (
                poly_ref_client.get_page_by_url(url)
                if url
                else poly_ref_client.get_tickers(
                    market="stocks", active=True, symbol_type=CS, exchange=exchange
                )
            )
            log.info(
                f"Response Status: {response.get('status')},Count :{response.get('count')} Next URL: {response.get('next_url')}"
            )
            filtered_tickers = [
                i
                for i in response.get("results", [])
                if i["primary_exchange"] == exchange
            ]
            log.info(f"Filtered tickers count: {len(filtered_tickers)}")
            tickers.extend(filtered_tickers)
            if not (url := response.get("next_url")):
                break
    return tickers


def ticker_outstanding_shares(ticker) -> pd.DataFrame:
    """Fetch shares outstanding for a single ticker."""
    stock_info = {}
    try:
        ticker_info = yf.Ticker(ticker).info
        if not ticker_info or not isinstance(ticker_info, dict):
            log.warning(f"No Ticker info found for: `{ticker}`.")
            return pd.DataFrame()

        stock_info[SHARES] = ticker_info["sharesOutstanding"]
        stock_info[INDUSTRY] = ticker_info["industry"]
        stock_info[SECTOR] = ticker_info["sector"]
        stock_info[DISPLAY_NAME] = ticker_info["displayName"]
        stock_info[TICKER] = ticker

    except Exception as e:
        log.error(f"Error fetching shares outstanding for ticker {ticker}: {e}")
    return stock_info


def _fetch_ticker_history(ticker_batch, period) -> pd.DataFrame:
    """Fetch history for a single ticker."""
    tickers = yf.Tickers(ticker_batch, session=session)
    historical_data: pd.DataFrame = tickers.history(period=period, timeout=20)
    return historical_data


def fetch_ticker_history(ticker_batch, period="30d"):
    try:
        log.info(f"Count of ticker data to be fetched:{len(ticker_batch)}.")
        data = _fetch_ticker_history(ticker_batch, period)
        if data.empty:
            log.warning(f"No data returned for ticker batch: {ticker_batch}")
        return data
    except Exception as e:
        log.error(f"Error fetching data for ticker batch {ticker_batch}: {e}")
        return None
