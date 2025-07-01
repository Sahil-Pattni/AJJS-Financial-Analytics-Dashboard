import streamlit as st
from streamlit import session_state as ss
import pandas as pd
from enum import Enum
from src.backend.analytics import Analytics
from src.backend.plots import Plots


oz_to_gram = lambda x: x * (3.6725 / 31.1034768)

st.title("Financial Analysis")

# ----- OPTIONS ----- #
toggle = st.sidebar.toggle("Convert Gold Gains to Cash", value=False)
gold_rate = st.sidebar.number_input(
    "Gold Rate ($/ounce)", min_value=0.0, value=3348.66, step=1.0
)
kwargs = {"convert_gold": toggle, "gold_rate": oz_to_gram(gold_rate)}
ignore_salaries = st.sidebar.toggle("Exclude Salaries", value=False)
# ----- DATA ----- #
fig = Plots.income_expenses_chart(
    Analytics.income_expenses_data(
        ss["wingold"].sales,
        ss["cashbook"].cashbook,
        ss["cashbook"].fixed_costs,
        **kwargs
    )
)

st.plotly_chart(fig, use_container_width=True)


st.subheader("Expenses Expansion")
fig = Plots.fixed_costs_sunburst(
    Analytics.fixed_cost_pie_chart_data(
        ss["cashbook"].cashbook, ss["cashbook"].fixed_costs
    ),
    ignore_salaries=ignore_salaries,
)
st.plotly_chart(fig, use_container_width=True, on_click="rerun")
