import pandas as pd
import plotly.express as px
import streamlit as st

from hedge_it.commons import get_logger
from hedge_it.commons.constants import (
    CLOSE,
    DATE,
    DISPLAY_NAME,
    EQUAL_WEIGHTED_INDEX,
    STOCKS,
    TABLE_TOPM,
    TICKER,
    VALUE,
)
from hedge_it.connectors.fetcher import fetch_stocks
from hedge_it.dashboards.metrics import (
    day_composition_changes,
    display_percentage_change,
)
from hedge_it.processor.duck_db import (
    duckconn,
    get_stock_composition,
    persist_index_table,
    persist_stock_df,
    persist_top_mcap,
    query_equal_weighted_index,
)
from hedge_it.processor.ticker_processor import ticker_processor

from .exporter import download_pdf_button

log = get_logger()


def build_data(
    polygon_key: str,
    exchanges: list = ["XNYS"],
    stock_limit: int = 2000,
    chunk_size: int = 50,
):
    log.info(
        f"Building Data with stock_limit: {stock_limit}, chunk_size: {chunk_size}, exchanges: {exchanges}"
    )
    if "stocks" in st.session_state:
        log.info("Stocks Data Already Exists. Reusing")
        return
    ticker_stocks, ticker_shares = fetch_stocks(
        polygon_key, exchanges, stock_limit, chunk_size
    )
    stocks_df = ticker_processor(ticker_stocks, ticker_shares)
    persist_stock_df(stocks_df)
    st.session_state["stocks"] = True


def build_index(top_n: int = 100, stock_table_name: str = STOCKS):
    if "mcap" not in st.session_state:
        log.info("Creating Custom Index.")
        persist_top_mcap(top_n, stock_table_name)
        st.session_state["mcap"] = (
            duckconn().execute(f"SELECT * FROM {TABLE_TOPM}").fetchdf()
        )
    else:
        log.info("Market Cap Info Already Exists. Reusing")
    if "index" not in st.session_state:
        persist_index_table()
        st.session_state["index"] = query_equal_weighted_index()
    else:
        log.info("Index Already Exists. Reusing")
    return st.session_state["index"], st.session_state["mcap"], get_stock_composition()


def calculate_cumulative_returns(data: pd.DataFrame, value_column: str) -> float:
    initial_value = data[value_column].iloc[0]
    final_value = data[value_column].iloc[-1]
    cumulative_return = ((final_value - initial_value) / initial_value) * 100
    st.metric(label="Cumulative Returns", value=f"{cumulative_return:.2f}%")


def plot(poly_key: str):
    st.title("Equal-Weighted Index Dashboard")
    build_data(poly_key)
    index, mcap, composition = build_index()
    mcap
    fig = px.line(
        index,
        x=DATE,
        y=EQUAL_WEIGHTED_INDEX,
        title="Equal-Weighted Index Price Over Time",
    )
    st.plotly_chart(fig)

    st.subheader("Stock Composition on a Selected Date")
    selected_date = st.date_input("Select a Date", value=index[DATE].min())
    selected_date_data = composition[
        composition[DATE] == pd.Timestamp(selected_date)
    ].reset_index(drop=True)

    if not selected_date_data.empty:
        st.write(f"Stock Composition for {selected_date}:")
        st.dataframe(selected_date_data[[TICKER, DISPLAY_NAME, VALUE, CLOSE]])
    else:
        st.write("No data available for the selected date.")

    download_pdf_button(selected_date_data)

    st.subheader("Summary Metrics")
    calculate_cumulative_returns(index, EQUAL_WEIGHTED_INDEX)
    display_percentage_change(index, DATE, EQUAL_WEIGHTED_INDEX)
    day_composition_changes(mcap)
