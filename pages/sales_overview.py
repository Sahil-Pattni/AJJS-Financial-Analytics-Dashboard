import streamlit as st
from streamlit import session_state as ss
import pandas as pd
from src.backend.modules import Components

df = ss["wingold"].sales.copy()

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
        (df.DocDate >= pd.to_datetime(ss["START_DATE"]))
        & (df.DocDate <= pd.to_datetime(ss["END_DATE"]))
    ]
)
