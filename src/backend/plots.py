from enum import Enum
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging


class Color(Enum):
    """
    Enum for color codes used in Streamlit plots.
    """

    OLIVE_GREEN = "#A6B37D"
    DARK_GREY = "#393E46"
    DARK_RED = "#CD5656"
    RED = "#DD3E3E"
    BLACK = "#000000"


class Plots:

    @staticmethod
    def income_expenses_chart(monthly_data: pd.DataFrame) -> None:
        """
        Generates an income and expenses chart using Streamlit.

        Args:
            monthly_data (pd.DataFrame): DataFrame containing monthly income and expenses.
        """

        # ----- Plotting ----- #
        fig = go.Figure()

        # Income
        fig.add_trace(
            go.Bar(
                x=monthly_data.index,
                y=monthly_data["Total Income"],
                name="Total Income",
                marker_color=Color.OLIVE_GREEN.value,
                text=monthly_data["Total Income"].apply(lambda x: f"{x:,.2f} AED"),
                textposition="outside",
                hovertemplate=("Month: %{x}<br>" + "Total Income: %{y:,.2f} AED<br>"),
            )
        )

        # Expenses
        fig.add_trace(
            go.Bar(
                x=monthly_data.index,
                y=monthly_data["Total Cost"],
                name="Total Cost",
                marker_color=Color.DARK_RED.value,
                text=monthly_data["Total Cost"].apply(lambda x: f"{x:,.2f} AED"),
                textposition="outside",
                hovertemplate=("Month: %{x}<br>" + "Total Expenses: %{y:,.2f} AED<br>"),
            )
        )

        # Add line for average expenses
        avg = monthly_data["Net Profit"].mean()
        fig.add_hline(
            y=avg,
            line_dash="dash",
            line_color=Color.BLACK.value,
            annotation_text=f"Average Net Profit: {avg:,.2f} AED",
            annotation_position="top left",
            annotation_font_color=Color.BLACK.value,
            opacity=0.2,
        )

        # Fixed costs line
        fixed_cost = -monthly_data["Fixed Costs"].mean()
        fig.add_hline(
            y=fixed_cost,
            line_dash="dash",
            line_color=Color.BLACK.value,
            annotation_text=f"Monthly Fixed Cost: {fixed_cost:,.2f} AED",
            annotation_position="top left",
            annotation_font_color=Color.BLACK.value,
            opacity=0.2,
        )

        # Add line for net profit
        fig.add_trace(
            go.Scatter(
                x=monthly_data.index,
                y=monthly_data["Net Profit"],
                mode="lines+markers",
                name="Net Profit",
                line=dict(color=Color.DARK_GREY.value, width=2),
                hovertemplate=("Month: %{x}<br>" + "Net Profit: %{y:,.2f} AED<br>"),
            )
        )

        ymax = max(monthly_data["Total Income"].max() * 1.3, 300000)
        ymin = min(monthly_data["Total Cost"].min() * 1.3, -300000)

        logging.info(f"Y-axis range set to: {ymin} to {ymax}")

        # Formatting
        # Keep y-axis range -200K to 200K
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Amount(AED)",
            yaxis=dict(
                tickprefix="AED ",
                range=[ymin, ymax],  # Set y-axis range
            ),
            xaxis=dict(tickformat="%b %Y"),
            margin=dict(t=50, b=50, l=150, r=50),
            barmode="relative",
            height=600,
        )

        fig.update_xaxes(automargin=True)
        fig.update_yaxes(title_standoff=30, automargin=True)

        # Present chart
        return fig

    @staticmethod
    def fixed_costs_sunburst(expenses: pd.DataFrame, ignore_salaries=True) -> None:
        """
        Generates a sunburst chart of the expense categories.
        Ignores salaries.

        Args:
            expenses (pd.DataFrame): DataFrame containing expense categories and amounts.
            ignore_salaries (bool): Whether to ignore salaries in the chart.
        """

        # ----- Plotting ----- #
        fig = px.sunburst(
            (
                expenses[expenses["Sub-Category"] != "Salaries"]
                if ignore_salaries
                else expenses
            ),
            path=["Super-Category", "Sub-Category"],
            title=" ",
            values="Debit",
            color="Super-Category",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hover_data={"Super-Category": False, "Sub-Category": False, "Debit": False},
        )

        fig.update_traces(
            # text=expenses["Debit"].map(lambda x: f"AED {x:,.2f}"),
            textinfo="none",
            texttemplate=(
                "<b>%{label}</b><br>" + "AED %{value:,.2f}<br>" + "%{percentEntry:.1%}"
            ),
            textfont_size=10,
        )

        # Formatting
        fig.update_layout(
            title_x=0.5,
            width=800,
            height=600,
            margin=dict(t=50, b=50, l=100, r=50),
        )

        # Present chart
        return fig
