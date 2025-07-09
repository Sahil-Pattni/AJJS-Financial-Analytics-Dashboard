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
COLOR_C = "#dedb18"  # 21K

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

        breakeven_volume = breakeven / (1000 * (unit_revenue - cost_per_gram))
        max_vol = st.number_input(
            "Max Volume (kg)",
            min_value=0.0,
            step=1.0,
            value=max(20.0, np.ceil(breakeven_volume + 1)),
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

    for karat, rev in revenue.items():
        share = ss[f"share_{karat}"]
        rate = ss[f"rate_{karat}"]
        rev.extend(volume * (1000 * share * rate))

    fig = go.Figure()

    total_revenue = volume * unit_revenue * 1000
    total_costs = (volume * (1000 * cost_per_gram)) + ss.breakeven
    # Split into before / after breakeven
    idx = np.searchsorted(volume, breakeven_volume)

    vol_before = volume[: idx + 1]
    rev_before = total_revenue[: idx + 1]
    costs_before = total_costs[: idx + 1]

    vol_after = volume[idx:]
    rev_after = total_revenue[idx:]
    costs_after = total_costs[idx:]

    # Add Revenue (Loss)
    fig.add_trace(
        go.Scatter(
            x=vol_before,
            y=rev_before,
            mode="lines",
            name="Gross Revenue",
            line=dict(color=COLOR_A, width=2, dash="dot"),
        )
    )

    # Add Costs (Loss)
    fig.add_trace(
        go.Scatter(
            x=vol_before,
            y=costs_before,
            mode="lines",
            name="Total Costs (Loss)",
            fill="tonexty",
            line=dict(color="#F3722C", width=2, dash="solid"),
        )
    )

    # Add Revenue (Profit)
    fig.add_trace(
        go.Scatter(
            x=vol_after,
            y=rev_after,
            mode="lines",
            name="Gross Revenue",
            line=dict(color=COLOR_B, width=2, dash="dot"),
        )
    )

    # Add Costs (Profit)
    fig.add_trace(
        go.Scatter(
            x=vol_after,
            y=costs_after,
            mode="lines",
            name="Total Costs (Profit)",
            fill="tonexty",
            line=dict(color="#7CF32C", width=2, dash="solid"),
        )
    )

    # Add breakeven line
    fig.add_hline(
        y=ss.breakeven,
        line_dash="dash",
        line_color="#A7A6A6",
        annotation_text="Fixed Costs",
        annotation_position="bottom right",
    )

    # Add vertical line for when total revenue equals total costs
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
    st.latex(
        r"y = 1000x \left(\sum_{i=1}^{n} (K_{i,\text{share}} \cdot K_{i,\text{rate}}) - \text{cost per gram}\right)"
        + f"= {1000*(unit_revenue - cost_per_gram):,.2f}x"
    )
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
