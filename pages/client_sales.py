import streamlit as st
from streamlit import session_state as ss
import pandas as pd
from src.backend.modules import Components

df = ss["wingold"].sales.copy()

ss["CLIENT"] = st.sidebar.selectbox(
    "Select Client",
    df["TAName"].sort_values().unique(),
    index=12,
)

ss["START_DATE"] = st.sidebar.date_input(
    "Start Date",
    value=df["DocDate"].min().date(),
    min_value=df["DocDate"].min().date(),
    max_value=df["DocDate"].max().date(),
)
ss["END_DATE"] = st.sidebar.date_input(
    "End Date",
    value=df["DocDate"].max().date(),
    min_value=df["DocDate"].min().date(),
    max_value=df["DocDate"].max().date(),
)

Components.generate_sales_analytics(
    df[
        (df.TAName == ss["CLIENT"])
        & (df.DocDate >= pd.to_datetime(ss["START_DATE"]))
        & (df.DocDate <= pd.to_datetime(ss["END_DATE"]))
    ]
)
