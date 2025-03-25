import os
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from itertools import islice

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf
from fpdf import FPDF
from polygon import ReferenceClient
from pyrate_limiter import Duration, Limiter, RequestRate
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket

poly_ref_client = ReferenceClient(api_key="your-api-key")


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass


session = CachedLimiterSession(
    limiter=Limiter(RequestRate(100, Duration.SECOND)),
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance.cache"),
)


def fetch_ticker_history(ticker_batch, period) -> pd.DataFrame:
    """Fetch history for a single ticker."""
    tickers = yf.Tickers(ticker_batch, session=session)
    historical_data: pd.DataFrame = tickers.history(period=period)
    return historical_data


def fetch_ticker_outstanding_shares(ticker_batch, period=30) -> pd.DataFrame:
    shares_outstanding_dfs = []
    for ticker in ticker_batch:
        try:
            shares_outstanding = pd.DataFrame()
            shares_outstanding["shares"] = yf.Ticker(ticker).get_shares_full(
                pd.Timestamp.utcnow() - pd.Timedelta(days=period)
            )
            shares_outstanding.index = pd.date_range(
                end=pd.Timestamp.utcnow().date(),
                periods=len(shares_outstanding),
                freq="D",
            )[::-1]
            shares_outstanding = shares_outstanding.rename_axis("Date").reset_index()
            shares_outstanding["Ticker"] = ticker
            shares_outstanding_dfs.append(shares_outstanding)
        except Exception as e:
            print(f"Error fetching shares outstanding for ticker {ticker}: {e}")
    data = pd.concat(shares_outstanding_dfs, ignore_index=True)
    if data.empty:
        print(f"No data returned for ticker share: {ticker_batch}")
        return None
    return data


def fetch_ticker_history_with_name(ticker_batch, period="30d"):
    try:
        data = fetch_ticker_history(ticker_batch, period)
        if data.empty:
            print(f"No data returned for ticker batch: {ticker_batch}")
        return data
    except Exception as e:
        print(f"Error fetching data for ticker batch {ticker_batch}: {e}")
        return None


def chunked_iterable(iterable, size):
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk


def get_active_exchange_stock_ticker(*exchanges):
    tickers = []
    api_call_count = 0
    for exchange in exchanges:
        print(f"Getting tickers for exchange {exchange}")
        url = None
        while True:
            api_call_count += 1
            if api_call_count > 5:
                print(
                    f"Warning: API call count has exceeded 5 Free Polygon has limit of 5 Calls Per Minute. Current count: {api_call_count}"
                )

            response = (
                poly_ref_client.get_page_by_url(url)
                if url
                else poly_ref_client.get_tickers(
                    market="stocks", active=True, symbol_type="CS", exchange=exchange
                )
            )
            print(
                f"Response Status: {response.get('status')},Count :{response.get('count')} Next URL: {response.get('next_url')}"
            )
            filtered_tickers = [
                i
                for i in response.get("results", [])
                if i["primary_exchange"] == exchange
            ]
            print(f"Filtered tickers count: {len(filtered_tickers)}")
            tickers.extend(filtered_tickers)
            if not (url := response.get("next_url")):
                break
    return tickers


def process_ticker_data(ticker_stocks) -> pd.DataFrame:
    cols = ["Close", "Low", "High", "Volume", "Open"]
    melted_dfs = []
    for col in cols:
        melted_df = (
            ticker_stocks[col]
            .reset_index()
            .melt(id_vars=["Date"], var_name="Ticker", value_name=col)
            .reset_index(drop=True)
        )
        melted_dfs.append(melted_df)
    ticker_df = reduce(
        lambda left, right: pd.merge(left, right, on=["Date", "Ticker"]), melted_dfs
    )
    return ticker_df


def merge_ticker_and_shares(ticker_df, ticker_shares) -> pd.DataFrame:
    stocks_df = pd.merge(ticker_shares, ticker_df, on=["Date", "Ticker"], how="inner")
    stocks_df["MCap"] = stocks_df["shares"] * stocks_df["Close"]
    return stocks_df


def duckconn():
    return duckdb.connect("stocks.duckdb")


def persist_stock_df(stock_df: pd.DataFrame):
    duckconn().register("stock_df", stock_df)
    duckconn().execute("CREATE OR REPLACE TABLE stocks AS SELECT * FROM stock_df")


def persist_top_mcap():
    query = """SELECT 
            Date, 
            Ticker, 
            MCap, 
            Close
        FROM 
            stocks
        WHERE 
            Date >= CURRENT_DATE - INTERVAL 30 DAY
        QUALIFY ROW_NUMBER() OVER (PARTITION BY Date ORDER BY MCap DESC) <= 2
        ORDER BY 
            Date, 
            MCap DESC;"""
    duckconn().execute(f"""
        CREATE TABLE IF NOT EXISTS TopMcap AS 
        {query}
        """)


def persist_equal_weighted_index():
    index_query = """
    WITH StockWeights AS (
        SELECT 
            Date,
            Close,
            COUNT(*) OVER (PARTITION BY Date) AS StockCount
        FROM 
            TopMCap
    )
    SELECT 
        Date,
        SUM(Close / StockCount) AS EqualWeightedIndex
    FROM 
        StockWeights
    GROUP BY 
        Date
    ORDER BY 
        Date;"""
    duckconn().execute(index_query)


def fetch_data():
    if "stocks" in st.session_state:
        return
    tickers = get_active_exchange_stock_ticker("XNYS")
    ticker_names = [t["ticker"] for t in tickers]
    with ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
        res_stock = executor.map(
            fetch_ticker_history_with_name, chunked_iterable(ticker_names[:10], 100)
        )
        res_shares = executor.map(
            fetch_ticker_outstanding_shares, chunked_iterable(ticker_names[:10], 100)
        )
    valid_results = [df for df in res_stock if df is not None and not df.empty]
    if valid_results:
        ticker_stocks = pd.concat(valid_results, ignore_index=False)
    else:
        print("No valid data to concat stocks")
        ticker_stocks = pd.DataFrame()

    valid_results = [df for df in res_shares if df is not None and not df.empty]
    if valid_results:
        ticker_shares = pd.concat(valid_results, ignore_index=False)
    else:
        print("No valid data to concat shares")
        ticker_shares = pd.DataFrame()
    ticker_df = process_ticker_data(ticker_stocks)
    stocks_df = merge_ticker_and_shares(ticker_df, ticker_shares)
    st.session_state.stocks = stocks_df
    print(f"Stocks shape: {stocks_df.shape}")
    print(f"Type(stocks): {type(stocks_df)}")
    persist_stock_df(stocks_df)
    persist_top_mcap()
    persist_equal_weighted_index()
    return


def plot():
    st.title("Equal-Weighted Index Dashboard")
    if "mcap_df" not in st.session_state:
        st.session_state.mcap_df = duckconn().execute("SELECT * FROM TopMcap").fetchdf()
    index_query = """
    WITH StockWeights AS (
        SELECT 
            Date,
            Close,
            COUNT(*) OVER (PARTITION BY Date) AS StockCount
        FROM 
            TopMCap
    )
    SELECT 
        Date,
        SUM(Close / StockCount) AS EqualWeightedIndex
    FROM 
        StockWeights
    GROUP BY 
        Date
    ORDER BY 
        Date;"""
    if "equal_weighted_index" not in st.session_state:
        st.session_state.equal_weighted_index = (
            duckconn().execute(index_query).fetchdf()
        )
    mcap_df = st.session_state.mcap_df
    equal_weighted_index = st.session_state.equal_weighted_index
    # Plot the Equal-Weighted Index vs. Date
    st.subheader("Equal-Weighted Index Price vs. Date")
    fig = px.line(
        equal_weighted_index,
        x="Date",
        y="EqualWeightedIndex",
        title="Equal-Weighted Index Price Over Time",
    )
    st.plotly_chart(fig)

    # Display stock composition for a selected date
    st.subheader("Stock Composition on a Selected Date")
    selected_date = st.date_input(
        "Select a Date", value=equal_weighted_index["Date"].min()
    )
    selected_date_data = mcap_df[mcap_df["Date"] == pd.Timestamp(selected_date)]

    if not selected_date_data.empty:
        st.write(f"Stock Composition for {selected_date}:")
        st.dataframe(selected_date_data[["Ticker", "Close"]])
    else:
        st.write("No data available for the selected date.")
    pdf_file = generate_pdf(selected_date_data)
    if st.button("Download PDF"):
        with open(pdf_file, "rb") as f:
            st.download_button(
                label="Download PDF",
                data=f,
                file_name="stock_composition.pdf",
                mime="application/pdf",
            )


def generate_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add a title
    pdf.cell(200, 10, txt="Stock Data Report", ln=True, align="C")

    # Add table headers
    pdf.set_font("Arial", style="B", size=10)
    for column in dataframe.columns:
        pdf.cell(40, 10, column, border=1, align="C")
    pdf.ln()

    # Add table rows
    pdf.set_font("Arial", size=10)
    for _, row in dataframe.iterrows():
        for value in row:
            pdf.cell(40, 10, str(value), border=1, align="C")
        pdf.ln()

    # Save PDF to a file-like object
    pdf_output = "stock_composition.pdf"
    pdf.output(pdf_output)
    return pdf_output


if __name__ == "__main__":
    fetch_data()
    # persist_stock_df("stocks")
    # persist_top_mcap("stocks")
    # persist_equal_weighted_index("stocks")
    plot()
