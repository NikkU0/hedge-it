import pandas as pd
import streamlit as st

from hedge_it.commons.constants import DATE, TICKER


def display_percentage_change(data: pd.DataFrame, date_column: str, value_column: str):
    data = data.sort_values(by=date_column)
    data["Daily % Change"] = data[value_column].pct_change() * 100

    latest_change = data["Daily % Change"].iloc[-1]
    st.metric(
        label="Daily Percentage Change",
        value=f"{latest_change:.2f}%",
        delta=f"{latest_change:.2f}%",
    )
    st.write("Daily Percentage Changes")
    st.bar_chart(data.set_index(date_column)["Daily % Change"])


def day_composition_changes(mcap: pd.DataFrame):
    df = mcap.sort_values(by=DATE)
    df["Tickers_Set"] = df.groupby(DATE)[TICKER].transform(lambda x: tuple(sorted(x)))
    df["Composition_Changed"] = df["Tickers_Set"] != df["Tickers_Set"].shift()
    df = df.drop(columns=["Tickers_Set"])
    df = df[df["Composition_Changed"]].rename(columns={DATE: "Date"})["Date"].unique()
    st.write("Composition Change Days")
    st.write(df)
