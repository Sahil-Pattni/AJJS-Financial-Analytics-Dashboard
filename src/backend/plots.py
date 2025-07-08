from enum import Enum
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging
import streamlit as st
from scipy.signal import savgol_filter


class Color(Enum):
    """
    Enum for color codes used in Streamlit plots.
    """

    OLIVE_GREEN = "#A6B37D"
    DARK_GREY = "#393E46"
    DARK_RED = "#DA6C6C"
    RED = "#DD3E3E"
    BLACK = "#000000"
    GREEN1 = "#819A91"
    GREEN2 = "#A7C1A8"
    GREEN3 = "#D1D8BE"
    OCEAN_BLUE = "#003049"
    BLUE1 = "#415a77"
    BLUE2 = "#778da9"


class Plots:

    @staticmethod
    def income_expenses_chart(monthly_data: pd.DataFrame, convert_gold=False) -> None:
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
                name="Making Charges",
                marker_color=Color.GREEN1.value,
                text=monthly_data["Total Income"].apply(lambda x: f"{x:,.2f} AED"),
                textposition="outside",
                hovertemplate=("Month: %{x}<br>" + "Making Charges: %{y:,.2f} AED<br>"),
            )
        )

        if convert_gold:
            fig.add_trace(
                go.Bar(
                    x=monthly_data.index,
                    y=monthly_data["GoldGains"],
                    name="Gold Gains",
                    marker_color=Color.GREEN3.value,
                    text=monthly_data["GoldGains"].apply(lambda x: f"{x:,.2f} AED"),
                    textposition="outside",
                    hovertemplate=("Month: %{x}<br>" + "Gold Gains: %{y:,.2f} AED<br>"),
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
        profit = (
            monthly_data["Net Profit"]
            if not convert_gold
            else (
                (monthly_data["Total Income"] + monthly_data["GoldGains"])
                + monthly_data["Total Cost"]
            )
        )
        avg = profit.mean()
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
                y=profit,
                mode="lines+markers",
                name="Net Profit",
                line=dict(color=Color.DARK_GREY.value, width=2),
                hovertemplate=("Month: %{x}<br>" + "Net Profit: %{y:,.2f} AED<br>"),
            )
        )

        ymax = max(
            (monthly_data["Total Income"].max() + monthly_data["GoldGains"].max())
            * 1.3,
            400000,
        )
        ymin = min(monthly_data["Total Cost"].min() * 1.3, -330000)

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
            height=900,
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
            height=800,
            margin=dict(t=50, b=50, l=100, r=50),
        )

        # Present chart
        return fig

    @staticmethod
    def sales_sunburst(sales: pd.DataFrame, y: str = "MakingValue") -> None:
        """
        Generates a sunburst chart of the sales data.

        Args:
            sales (pd.DataFrame): DataFrame containing sales data.
        """

        # ----- Plotting ----- #
        pastel = px.colors.qualitative.Pastel
        fig = px.sunburst(
            sales,
            path=["PurityCategory", "ItemCategory"],
            values=y,
            color="PurityCategory",
            color_discrete_map={
                "18K": Color.BLUE1.value,
                "21K": pastel[1],
                "22K": Color.BLUE2.value,
                "9K": pastel[4],
            },
            width=800,
            height=600,
        )

        # Formatting
        fig.update_traces(
            texttemplate=(
                "<b>%{label} (%{percentEntry:.2%})</b><br>"
                + "%{value:,.2f}"
                + f" {'AED' if y == 'MakingValue' else 'g'}"
            ),
            textinfo="text",
            textfont_size=10,
        )
        fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))

        # Present chart
        return fig

    @staticmethod
    def monthwise_sales(sales: pd.DataFrame, y: str = "MakingValue") -> None:
        """
        Generates a month-wise sales chart by purity using Streamlit.

        Args:
            df (pd.DataFrame): Sales DataFrame.
        """

        # ----- Plotting ----- #
        pastel = px.colors.qualitative.Pastel
        fig = px.bar(
            sales,
            x=sales.Month,
            y=sales[y],
            color=sales.PurityCategory,
            custom_data=["PurityCategory"],
            color_discrete_map={
                "18K": Color.BLUE1.value,
                "21K": pastel[1],
                "22K": Color.BLUE2.value,
                "9K": pastel[4],
            },
            # title="Monthly Sales by Purity",
            barmode="stack",
            height=600,
            width=800,
        )
        avg_making = (
            sales.groupby(sales.Month).agg({"MakingValue": "sum"})["MakingValue"].mean()
        )
        fig.add_hline(
            y=avg_making,
            line_dash="dash",
            line_color=Color.BLACK.value,
            annotation_text=f"Average Income: {avg_making:,.2f} AED",
            annotation_position="top right",
            annotation_font_color=Color.BLACK.value,
            opacity=0.2,
        )

        base_ymax = 130000
        base_ythresh = 100000
        sales_max = sales.groupby(sales.Month).agg({y: "sum"})[y].max() * 1.2
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Making Charges (AED)",
            legend_title_text="Purity Category",
            xaxis=dict(tickformat="%b %Y"),
            yaxis=dict(
                range=[
                    0,
                    (
                        max(base_ymax, sales_max)
                        if sales_max > base_ythresh and y != "GrossWt"
                        else sales_max
                    ),
                ],
            ),
        )

        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Purity: %{customdata[0]}<br>Making Value: %{y:,.2f}<extra></extra>",
        )

        # Present chart
        return fig

    @staticmethod
    def weekly_monthly_boxplot(df: pd.DataFrame) -> None:
        """
        Generates a boxplot of weekly making charges by month.

        Args:
            df (pd.DataFrame): DataFrame containing sales data.
        """

        # ----- Plotting ----- #
        data = df[df.TransactionType == "SALE"].copy()
        data["Month"] = data.DocDate.dt.to_period("M").astype(str)
        data["Week"] = data.DocDate.dt.to_period("W")
        data = (
            data[data.MakingValue > 0]
            .groupby(["Month", "Week"])
            .agg({"MakingValue": "sum"})
            .reset_index()
        )
        data.columns = ["Month", "Week", "MakingValue"]

        fig = px.box(
            data,
            x="Month",
            y="MakingValue",
            title="Weekly Making Charges by Month",
            labels={"Month": "Month", "MakingValue": "Making Charges (AED)"},
            width=800,
            height=600,
            color_discrete_sequence=[Color.OCEAN_BLUE.value],
        )

        # Uncomment below to remove inside fill color

        fig.update_traces(
            fillcolor="rgba(131,152,163,255)",
            line_width=2,
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Making Charges (AED)",
        )

        # Present chart
        return fig

    @staticmethod
    def sales_histogram(sales: pd.DataFrame) -> None:
        """
        Generates a histogram of sales data.

        Args:
            sales (pd.DataFrame): DataFrame containing sales data.
        """

        fig = px.histogram(
            sales,
            x="Day",
            y="GrossWt",
            nbins=50,
            # labels={"MakingValue": "Making Value"},
            color_discrete_sequence=[Color.OCEAN_BLUE.value],
            title="Weekly Distribution of Gross Weight",
        )

        # Add a rolling average line
        weekly = sales.copy()

        weekly = (
            weekly.resample("W", on="DocDate").agg({"GrossWt": "sum"}).reset_index()
        )
        weekly["RollingAvg"] = (
            weekly["GrossWt"].rolling(window=4, win_type="triang").mean()
        )
        # Backfill
        weekly["RollingAvg"] = weekly["RollingAvg"].bfill()

        fig.add_trace(
            go.Scatter(
                x=weekly["DocDate"],
                y=savgol_filter(weekly["RollingAvg"], 10, 2),
                mode="lines",
                name="Weekly Average",
                line=dict(color=Color.DARK_RED.value, width=2),
                hovertemplate=(
                    "Week: %{x}<br>" + "Average Gross Weight: %{y:.2f} g<br>"
                ),
            )
        )

        fig.update_traces(
            marker_line_width=2,
            marker_line_color="black",
            marker_color="rgba(131,152,163,255)",
        )

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="black"),
            xaxis=dict(showgrid=False, zeroline=False, gridcolor="lightgray"),
            yaxis=dict(showgrid=True, zeroline=False, gridcolor="lightgray"),
            xaxis_title="Week",
            yaxis_title="Gross Weight (g)",
            width=1000,
            height=600,
            legend=dict(
                x=0.98,  # 98% from the left of the plotting area
                y=0.98,  # 98% from the bottom (i.e. near the top)
                xanchor="right",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.6)",  # semi-transparent white bg
                bordercolor="black",
                borderwidth=1,
            ),
        )

        return fig

    @staticmethod
    def item_weight_boxplot(
        sales: pd.DataFrame, purity=None, item_category=None
    ) -> None:
        """
        Generates a boxplot of item weights by item category.

        Args:
            sales (pd.DataFrame): DataFrame containing sales data.
        """

        data = sales[(sales.TransactionType == "SALE")]

        if item_category:
            data = data[data.ItemCategory == item_category]
        if purity:
            data = data[data.PurityCategory == purity]

        # ----- Plotting ----- #
        fig = px.box(
            data.loc[data.index.repeat(data.QtyInPcs)]
            .reset_index(drop=True)
            .groupby(["ItemCategory", "Month", "Week"])
            .agg({"ItemWeight": "median"})
            .reset_index(),
            x="Month",
            y="ItemWeight",
            title=f"Median Weekly Item Weight by Month: {item_category if item_category else 'All Items'}",
            labels={"ItemCategory": "Item Category", "ItemWeight": "Item Weight (g)"},
            color_discrete_sequence=[Color.OCEAN_BLUE.value],
            # points=False,
        )

        fig.update_traces(
            fillcolor="rgba(131,152,163,255)",
            line_width=2,
        )

        fig.update_layout(
            xaxis_title="Item Category",
            yaxis_title="Item Weight (g)",
        )

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="black"),
            xaxis=dict(showgrid=False, zeroline=False, gridcolor="lightgray"),
            yaxis=dict(showgrid=True, zeroline=False, gridcolor="lightgray"),
            width=1000,
            height=600,
        )

        # Present chart
        return fig

    @staticmethod
    def item_weight_distribution(
        sales: pd.DataFrame, item_category=None, purity=None, nbins=50, normalize=False
    ) -> None:
        """
        Generates a histogram of item weights by item category.

        Args:
            sales (pd.DataFrame): DataFrame containing sales data.
        """

        data = sales[(sales.TransactionType == "SALE")]
        if item_category:
            data = data[data.ItemCategory == item_category]
        if purity:
            data = data[data.PurityCategory == purity]
        # ----- Plotting ----- #
        fig = px.histogram(
            data,
            x="ItemWeight",
            y="MakingValue",
            histfunc="sum",
            nbins=nbins,
            title=f"Weight Distribution: {item_category if item_category else 'All Items'}",
            color_discrete_sequence=[Color.OCEAN_BLUE.value],
            barmode="relative",
        )

        fig.update_traces(
            marker_line_width=2,
            marker_color="rgba(131,152,163,255)",
        )

        if normalize:
            fig.update_traces(histnorm="percent")

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="black"),
            xaxis=dict(showgrid=False, zeroline=False, gridcolor="lightgray"),
            yaxis=dict(showgrid=True, zeroline=False, gridcolor="lightgray"),
            yaxis_title="Percent (%)" if normalize else "Making Value (AED)",
            xaxis_title="Item Weight (g)",
            width=1000,
            height=600,
        )

        # Present chart
        return fig
