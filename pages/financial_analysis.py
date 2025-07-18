import streamlit as st
from streamlit import session_state as ss
import pandas as pd
from enum import Enum
from src.backend.analytics import Analytics
from src.backend.plots import Plots


oz_to_gram = lambda x: x * (3.6725 / 31.1034768)

st.title("Financial Analysis")

# ----- OPTIONS ----- #
convert_gold = st.sidebar.toggle("Convert Gold Gains to Cash", value=True)
include_qtr = st.sidebar.toggle("Include QTR Data", value=True)
gold_rate = st.sidebar.number_input(
    "Gold Rate ($/ounce)", min_value=0.0, value=3348.66, step=1.0
)
kwargs = {"gold_rate": oz_to_gram(gold_rate)}
ignore_salaries = st.sidebar.toggle("Exclude Salaries", value=True)

# ----- DATA ----- #
sales = ss["sales"].data
if not include_qtr:
    sales = sales[sales["QTR"] == False]

tabs = st.tabs(["Income/Expenses", "Profit/Loss"])
financial_data = Analytics.income_expenses_data(
    sales, ss["cashbook"].cashbook, ss["cashbook"].fixed_costs, **kwargs
)
with tabs[0]:
    fig = Plots.income_expenses_chart(
        financial_data,
        convert_gold=convert_gold,
    )
    st.plotly_chart(fig, use_container_width=True)
with tabs[1]:
    fig = Plots.profit_loss_barchart(
        financial_data,
        convert_gold=convert_gold,
    )
    st.plotly_chart(fig, use_container_width=True)

p, q = st.columns(2)
with p:
    st.subheader("Fixed Costs")
    fig = Plots.costs_sunburst(
        Analytics.fixed_cost_pie_chart_data(ss["cashbook"]),
        ignore_salaries=ignore_salaries,
    )
    st.plotly_chart(fig, use_container_width=True, on_click="rerun")

with q:
    st.subheader("Variable Costs")
    fig = Plots.costs_sunburst(
        Analytics.variable_cost_pie_chart_data(ss["cashbook"]),
        ignore_salaries=False,
        variable=True,
    )
    st.plotly_chart(fig, use_container_width=True, on_click="rerun")
