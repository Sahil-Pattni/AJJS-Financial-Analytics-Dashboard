import streamlit as st
from streamlit import session_state as ss
import pandas as pd
from src.backend.modules import Components

df = ss["sales"].data.copy()

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

ss["START_DATE"] = st.sidebar.date_input(
    "Start Date",
    value=min_date,
    min_value=min_date,
    max_value=max_date,
)
ss["END_DATE"] = st.sidebar.date_input(
    "End Date",
    value=max_date,
    min_value=min_date,
    max_value=max_date,
)

Components.generate_sales_page(
    df[
        (df.Date >= pd.to_datetime(ss["START_DATE"]))
        & (df.Date <= pd.to_datetime(ss["END_DATE"]))
    ]
)
