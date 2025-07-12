import streamlit as st
from streamlit import session_state as ss
import pandas as pd
from src.backend.modules import Components

df = ss["sales"].data.copy()
clients = df["TAName"].sort_values().unique().tolist()
ss["CLIENT"] = st.sidebar.selectbox(
    "Select Client", clients, index=clients.index("Meena Jewellers LLC")
)

min_date = df["DocDate"].min().date()
max_date = df["DocDate"].max().date()

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

st.title(ss.CLIENT)
Components.generate_sales_page(
    df[
        (df.TAName == ss["CLIENT"])
        & (df.DocDate >= pd.to_datetime(ss["START_DATE"]))
        & (df.DocDate <= pd.to_datetime(ss["END_DATE"]))
    ]
)
