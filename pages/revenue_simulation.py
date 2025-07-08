import streamlit as st
from streamlit import session_state as ss
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

load_dotenv()


with st.sidebar:
    with st.container(border=True):
        st.markdown("### Simulation Settings")
        share_18 = st.slider(
            "18K Share of Volume",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            value=0.3,
            key="share_18k",
            on_change=lambda: ss.update({"share_22k": 1 - ss.share_18k}),
        )

        share_22 = st.slider(
            "22K Share of Volume",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            value=0.7,
            key="share_22k",
            on_change=lambda: ss.update({"share_18k": 1 - ss.share_22k}),
        )

        rate_18 = st.number_input(
            "18K Rate",
            min_value=0.0,
            step=0.5,
            value=float(os.getenv("18K_rate")),
            key="rate_18k",
        )

        rate_22 = st.number_input(
            "22K Rate",
            min_value=0.0,
            step=0.5,
            value=float(os.getenv("22K_rate")),
            key="rate_22k",
        )

        max_vol = st.number_input(
            "Max Volume (kg)",
            min_value=0,
            step=1,
            value=20,
            key="max_vol",
        )

        breakeven = st.number_input(
            "Breakeven Point (AED)",
            min_value=0,
            max_value=500000,
            step=100,
            value=int(os.getenv("monthly_fixed_costs")),
            key="breakeven",
        )

# ----- SIMULATION LOGIC ----- #
revenue = {
    "18k": [],
    "22k": [],
}

volume = np.arange(0, ss.max_vol + 0.5, 0.2)

for kg in volume:
    for karat, rev in revenue.items():
        share = ss[f"share_{karat}"]
        rate = ss[f"rate_{karat}"]
        rev.append(kg * 1000 * share * rate)

total_revenue = np.array(revenue["18k"]) + np.array(revenue["22k"])

unit_revenue = 1000 * ((ss.share_18k * ss.rate_18k) + (ss.share_22k * ss.rate_22k))

fig = go.Figure()

# Add 18K
fig.add_trace(
    go.Scatter(
        x=volume,
        y=revenue["18k"],
        mode="lines",
        name="18K Revenue",
        line=dict(color="#EABDB3", width=2, dash="dot"),
    )
)

# Add 22K
fig.add_trace(
    go.Scatter(
        x=volume,
        y=revenue["22k"],
        mode="lines",
        name="22K Revenue",
        line=dict(color="#4FBC75", width=2, dash="dot"),
    )
)

# Add Total Revenue
fig.add_trace(
    go.Scatter(
        x=volume,
        y=total_revenue,
        mode="lines",
        name="Total Revenue",
        fill="tozeroy",
        fillcolor="rgba(116, 141, 169, 0.2)",
        line=dict(color="#778da9", width=2, dash="solid"),
    )
)

# Add breakeven line
fig.add_hline(
    y=ss.breakeven,
    line_dash="dash",
    line_color="#F3722C",
    annotation_text="Break-Even Point",
    annotation_position="top left",
)

# Add vertical line for when total revenue equals breakeven
breakeven_volume = volume[np.where(total_revenue >= ss.breakeven)[0][0]]
fig.add_vline(
    x=breakeven_volume,
    line_dash="dash",
    line_color="#F3722C",
    annotation_text=f"Break-Even Volume: {breakeven_volume:.1f} kg",
    annotation_position="top right",
)

fig.update_layout(
    xaxis_title="Volume (kg)",
    yaxis_title="Revenue (AED)",
    legend=dict(x=0.01, y=0.99),
    template="plotly_white",
    width=800,
    height=650,
)

fig.update_traces(
    hovertemplate="<b>Volume: %{x:,.1f} kg<br>Revenue%{y:,.2f} AED</b><extra></extra>",
)

st.title("Revenue Simulation")
st.info(f"1 KG = {unit_revenue:,.2f} AED")
st.plotly_chart(fig, use_container_width=False)
