import streamlit as st
from streamlit import session_state as ss
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

load_dotenv()

COLOR_A = "#457b9d"  # 18K
COLOR_B = "#a8dadc"  # 22K
COLOR_C = "#e63946"  # 21K

sales = ss["wingold"].sales
cb = ss["cashbook"].cashbook
cost_per_gram = (
    cb[cb["Cost Type"] == "VARIABLE"]["Debit"].sum() / sales["GrossWt"].sum()
)


def karat_settings(karat: str, value=0.3):
    with st.container(border=True):
        st.markdown(f"##### {karat}K Settings")
        share = st.slider(
            f"{karat}K Share of Volume",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            value=value,
            key=f"share_{karat}k",
        )

        rate = st.number_input(
            f"{karat}K Rate",
            min_value=0.0,
            step=0.5,
            value=float(os.getenv(f"{karat}K_rate", 0.0)),
            key=f"rate_{karat}k",
        )


with st.sidebar:
    with st.container(border=True):
        st.markdown("### Simulation Settings")
        karat_settings("18", value=0.3)
        karat_settings("22", value=0.5)
        karat_settings("21", value=0.2)

        cost_per_gram = st.number_input(
            "Cost per Gram (AED)",
            min_value=0.0,
            step=0.1,
            value=cost_per_gram,
            key="cost_per_gram",
        )

        breakeven = st.number_input(
            "Breakeven Point (AED)",
            min_value=0,
            max_value=500000,
            step=100,
            value=int(os.getenv("monthly_fixed_costs")),
            key="breakeven",
        )

        unit_revenue = 0
        for karat in ["18k", "22k", "21k"]:
            unit_revenue += ss[f"share_{karat}"] * ss[f"rate_{karat}"]

        min_volume = breakeven / (1000 * (unit_revenue - cost_per_gram))
        max_vol = st.number_input(
            "Max Volume (kg)",
            min_value=0.0,
            step=1.0,
            value=max(20.0, min_volume + 1),
            key="max_vol",
        )


# ----- SIMULATION LOGIC ----- #
def simulate():
    revenue = {
        "18k": [],
        "22k": [],
        "21k": [],
    }

    volume = np.arange(0, ss.max_vol + 0.5, 0.2)

    for kg in volume:
        for karat, rev in revenue.items():
            share = ss[f"share_{karat}"]
            rate = ss[f"rate_{karat}"]
            rev.append((kg * 1000 * share) * (rate - ss.cost_per_gram))
    total_revenue = (
        np.array(revenue["18k"]) + np.array(revenue["22k"]) + np.array(revenue["21k"])
    )

    fig = go.Figure()

    # Add 18K
    fig.add_trace(
        go.Scatter(
            x=volume,
            y=revenue["18k"],
            mode="lines",
            name="18K Revenue",
            fill="tonexty",
            line=dict(color=COLOR_A, width=2, dash="dot"),
        )
    )

    # Add 22K
    fig.add_trace(
        go.Scatter(
            x=volume,
            y=np.array(revenue["22k"]) + np.array(revenue["18k"]),
            mode="lines",
            fill="tonexty",
            name="22K Revenue",
            line=dict(color=COLOR_B, width=2, dash="dot"),
        )
    )

    # Add 21K
    fig.add_trace(
        go.Scatter(
            x=volume,
            y=np.array(revenue["21k"])
            + np.array(revenue["22k"])
            + np.array(revenue["18k"]),
            mode="lines",
            fill="tonexty",
            name="21K Revenue",
            line=dict(color=COLOR_C, width=2, dash="dot"),
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
    if breakeven_volume > ss.max_vol:
        ss.max_vol = breakeven_volume + 1
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
    st.info(f"1 KG = {unit_revenue:,.2f} AED")
    st.plotly_chart(fig, use_container_width=True)

    return revenue


if ss.get("share_18k") + ss.get("share_22k") + ss.get("share_21k") != 1.0:
    st.error("The total share of 18K, 22K, and 21K must equal 1.0.")
else:
    st.title("Revenue Simulation")
    q, y = st.columns([1, 1])
    with q:
        revenue = simulate()
    with y:
        fig = go.Figure()
        fig.add_trace(
            go.Pie(
                labels=["18K", "22K", "21K"],
                values=[
                    revenue["18k"][-1],
                    revenue["22k"][-1],
                    revenue["21k"][-1],
                ],
                hole=0.4,
                textinfo="label+percent",
                marker=dict(colors=[COLOR_A, COLOR_B, COLOR_C]),
            )
        )
        fig.update_layout(
            # title="Revenue Distribution by Karat",
            # legend=dict(x=0.01, y=0.99),
            template="plotly_white",
            height=650,
        )

        st.info("Revenue Distribution by Karat")
        st.plotly_chart(fig, use_container_width=True)
