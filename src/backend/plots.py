from enum import Enum
from typing import List
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging
import streamlit as st
from scipy.signal import savgol_filter
from datetime import datetime

from src.backend.analytics import Analytics


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
    K18 = "#003049"
    K22 = "#9f111a"
    K21 = "#ffc300"
    K9 = "#02b013"


class Plots:

    @staticmethod
    def profit_loss_barchart(monthly_data: pd.DataFrame, convert_gold=False) -> None:
        """
        Generates a profit and loss bar chart using Streamlit.

        Args:
            monthly_data (pd.DataFrame): DataFrame containing monthly income and expenses.
            convert_gold (bool): Whether to convert gold gains to cash. Defaults to False.
        """

        # ----- Plotting ----- #
        df = monthly_data.copy()
        df["Profit"] = (
            monthly_data["Net Profit"]
            if not convert_gold
            else (
                (monthly_data["Total Income"] + monthly_data["Gold Gains"])
                + monthly_data["Total Cost"]
            )
        )
        df["Direction"] = df["Profit"].apply(
            lambda x: "Net Profit" if x >= 0 else "Net Loss"
        )

        fig = px.bar(
            df,
            y="Profit",
            color="Direction",
            color_discrete_map={
                "Net Profit": Color.GREEN1.value,
                "Net Loss": Color.RED.value,
            },
            text="Profit",
            title="Monthly Profit and Loss",
            labels={"Profit": "Profit/Loss (AED)"},
        )
        fig.update_traces(texttemplate="%{text:,.2f} AED", textposition="outside")

        ymax = max(
            (df["Profit"].max()) * 1.3,
            30000,
        )
        ymin = min(df["Profit"].min() * 1.3, -150000)
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Profit/Loss (AED)",
            yaxis=dict(tickprefix="AED ", range=[ymin, ymax]),
            xaxis=dict(tickformat="%b %Y"),
            height=600,
            width=800,
        )
        fig.update_xaxes(automargin=True)
        fig.update_yaxes(title_standoff=30, automargin=True)

        # Present chart
        return fig

    @staticmethod
    def income_expenses_chart(monthly_data: pd.DataFrame, convert_gold=False) -> None:
        """
        Generates an income and expenses chart using Streamlit.

        Args:
            monthly_data (pd.DataFrame): DataFrame containing monthly income and expenses.
        """

        # ----- DERIVED STATS & DATA ----- #
        # Add line for average expenses
        profit = (
            monthly_data["Net Profit"]
            if not convert_gold
            else (
                (monthly_data["Total Income"] + monthly_data["Gold Gains"])
                + monthly_data["Total Cost"]
            )
        )
        avg = profit.mean()

        # ----- Plotting ----- #
        fig = go.Figure()

        # Income
        fig.add_trace(
            go.Bar(
                y=monthly_data["Total Income"],
                name="Making Charges",
                marker_color=Color.GREEN1.value,
                text=monthly_data["Total Income"].apply(lambda x: f"{x:,.2f} AED"),
                hovertemplate=("Month: %{x}<br>" + "Making Charges: %{y:,.2f} AED<br>"),
            )
        )

        # Add gold gains as AED
        if convert_gold:
            fig.add_trace(
                go.Bar(
                    y=monthly_data["Gold Gains"],
                    name="Gold Gains",
                    marker_color=Color.GREEN3.value,
                    text=monthly_data["Gold Gains"].apply(lambda x: f"{x:,.2f} AED"),
                    hovertemplate=("Month: %{x}<br>" + "Gold Gains: %{y:,.2f} AED<br>"),
                )
            )

        # Expenses
        fig.add_trace(
            go.Bar(
                y=monthly_data["Total Cost"],
                name="Total Cost",
                marker_color=Color.DARK_RED.value,
                text=monthly_data["Total Cost"].apply(lambda x: f"{x:,.2f} AED"),
                hovertemplate=("Month: %{x}<br>" + "Total Expenses: %{y:,.2f} AED<br>"),
            )
        )

        # Common trace args
        fig.update_traces(textposition="outside")

        # Add line for net profit
        fig.add_trace(
            go.Scatter(
                y=profit,
                mode="lines+markers",
                name="Net Profit",
                line=dict(color=Color.DARK_GREY.value, width=2),
                hovertemplate=("Month: %{x}<br>" + "Net Profit: %{y:,.2f} AED<br>"),
            )
        )

        # Common trace args
        fig.update_traces(x=monthly_data.index)

        # Common line args
        kwargs = {
            "line_dash": "dash",
            "line_color": Color.BLACK.value,
            "annotation_position": "top left",
            "annotation_font_color": Color.BLACK.value,
            "opacity": 0.2,
        }

        fig.add_hline(
            y=avg, annotation_text=f"Average Net Profit: {avg:,.2f} AED", **kwargs
        )

        # Fixed costs line
        fixed_cost = -monthly_data["Fixed Costs"].mean()
        fig.add_hline(
            y=fixed_cost,
            annotation_text=f"Monthly Fixed Cost: {fixed_cost:,.2f} AED",
            **kwargs,
        )

        ymax = max(
            (monthly_data["Total Income"].max() + monthly_data["Gold Gains"].max())
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
    def costs_sunburst(
        expenses: pd.DataFrame, ignore_salaries=True, variable=False
    ) -> None:
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
            path=(
                ["Super-Category", "Sub-Category"]
                if not variable
                else ["Sub-Category", "Category"]
            ),
            title=" ",
            values="Debit",
            color="Super-Category" if not variable else "Sub-Category",
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
    def _purity_color_map():
        return {
            "18K": Color.K18.value,
            "21K": Color.K21.value,
            "22K": Color.K22.value,
            "9K": Color.K9.value,
        }

    @staticmethod
    def sales_sunburst(sales: pd.DataFrame, y: str = "Making Value") -> None:
        """
        Generates a sunburst chart of the sales data.

        Args:
            sales (pd.DataFrame): DataFrame containing sales data.
        """

        # ----- Plotting ----- #
        fig = px.sunburst(
            sales,
            path=["Purity Category", "Item Category"],
            values=y,
            color="Purity Category",
            color_discrete_map=Plots._purity_color_map(),
            width=800,
            height=600,
        )

        # Formatting
        fig.update_traces(
            texttemplate=(
                "<b>%{label} (%{percentEntry:.2%})</b><br>"
                + "%{value:,.2f}"
                + f" {'AED' if y == 'Making Value' else 'g'}"
            ),
            textinfo="text",
            textfont_size=10,
        )
        fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))

        # Present chart
        return fig

    @staticmethod
    def monthwise_sales(sales: pd.DataFrame, y: str = "Making Value") -> None:
        """
        Generates a month-wise sales chart by purity using Streamlit.

        Args:
            df (pd.DataFrame): Sales DataFrame.
        """

        # ----- Plotting ----- #
        fig = px.bar(
            sales,
            x=sales.Month,
            y=sales[y],
            color=sales["Purity Category"],
            custom_data=["Purity Category"],
            color_discrete_map=Plots._purity_color_map(),
            # title="Monthly Sales by Purity",
            barmode="stack",
            height=600,
            width=800,
        )

        # Average sales
        avg = sales.groupby(sales.Month).agg({y: "sum"})
        # Exclude latest month if it is incomplete
        this_month = datetime.now().strftime("%Y-%m")
        if sales.Month.max() == this_month:
            avg = avg[avg.index != this_month]
        avg = avg[y].mean()

        fig.add_hline(
            y=avg,
            line_dash="dash",
            line_color=Color.BLACK.value,
            annotation_text=f"Average: {avg:,.2f} AED",
            annotation_position="top right",
            annotation_font_color=Color.BLACK.value,
            opacity=0.2,
        )

        base_ymax = 130000
        base_ythresh = 100000
        sales_max = sales.groupby(sales.Month).agg({y: "sum"})[y].max() * 1.2

        kwargs = {
            "showspikes": True,
            "spikecolor": "black",
            "spikethickness": 1,
            "spikedash": "solid",
            "spikemode": "across",  # Extend across full height
            "spikesnap": "cursor",
        }
        fig.update_layout(
            hovermode="closest",
            xaxis_title="Month",
            yaxis_title=(
                f"Making Charges (AED)" if y == "Making Value" else "Gross Weight (g)"
            ),
            legend_title_text="Purity Category",
            xaxis=dict(tickformat="%b %Y"),
            yaxis=dict(
                range=[
                    0,
                    (
                        max(base_ymax, sales_max)
                        if sales_max > base_ythresh and y != "Gross Weight"
                        else sales_max
                    ),
                ],
                **kwargs,
                dtick=20000 if y == "Making Value" else 2000,
            ),
        )

        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Purity: %{customdata[0]}<br>Value: %{y:,.2f}<extra></extra>",
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
        data = df[df["Transaction Type"] == "SALE"].copy()
        data["Month"] = data.Date.dt.to_period("M").astype(str)
        data["Week"] = data.Date.dt.to_period("W")
        data = (
            data[data["Making Value"] > 0]
            .groupby(["Month", "Week"])
            .agg({"Making Value": "sum"})
            .reset_index()
        )
        data.columns = ["Month", "Week", "Making Value"]

        fig = px.box(
            data,
            x="Month",
            y="Making Value",
            title="Weekly Making Charges by Month",
            labels={"Month": "Month", "Making Value": "Making Charges (AED)"},
            width=800,
            height=600,
            color_discrete_sequence=[Color.OCEAN_BLUE.value],
        )

        # Uncomment below to remove inside fill color

        fig.update_traces(
            fillcolor="rgba(0, 48, 73,0.7)",
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
            y="Gross Weight",
            nbins=50,
            # labels={" Making Value ": "Making Value"},
            title="Weekly Distribution of Gross Weight",
        )

        # Add a rolling average line
        weekly = sales.copy()

        weekly = (
            weekly.resample("W", on="Date").agg({"Gross Weight": "sum"}).reset_index()
        )
        weekly["RollingAvg"] = (
            weekly["Gross Weight"].rolling(window=4, win_type="triang").mean().bfill()
        )

        # Ignore savgol_filter if it fails
        try:
            fig.add_trace(
                go.Scatter(
                    x=weekly["Date"],
                    y=savgol_filter(weekly["RollingAvg"], 10, 2),
                    mode="lines",
                    name="Weekly Average",
                    line=dict(color=Color.DARK_RED.value, width=2),
                    hovertemplate=(
                        "Week: %{x}<br>" + "Average Gross Weight: %{y:.2f} g<br>"
                    ),
                )
            )
        except:
            logging.error("Error adding rolling average line to histogram.")

        fig.update_traces(
            marker_line_width=2,
            marker_line_color="black",
            marker_color="rgba(0, 48, 73,0.7)",
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

        data = sales[(sales["Transaction Type"] == "SALE")]

        if item_category:
            data = data[data["Item Category"] == item_category]
        if purity:
            data = data[data["Purity Category"] == purity]

        # ----- Plotting ----- #
        fig = px.box(
            data.loc[data.index.repeat(data["Unit Quantity"])]
            .reset_index(drop=True)
            .groupby(["Item Category", "Month", "Week"])
            .agg({"Item Weight": "median"})
            .reset_index(),
            x="Month",
            y="Item Weight",
            title=f"Median Weekly Item Weight by Month: {item_category if item_category else 'All Items'}",
            labels={"Item Category": "Item Category", "Item Weight": "Item Weight (g)"},
            color_discrete_sequence=[Color.OCEAN_BLUE.value],
            # points=False,
        )

        fig.update_traces(
            fillcolor="rgba(0, 48, 73,0.7)",
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

        data = sales[(sales["Transaction Type"] == "SALE")]
        if item_category:
            data = data[data["Item Category"] == item_category]
        if purity:
            data = data[data["Purity Category"] == purity]
        # ----- Plotting ----- #
        fig = px.histogram(
            data,
            x="Item Weight",
            y="Making Value",
            histfunc="sum",
            nbins=nbins,
            title=f"Weight Distribution: {item_category if item_category else 'All Items'}",
            color_discrete_sequence=[Color.OCEAN_BLUE.value],
            barmode="relative",
        )

        fig.update_traces(
            marker_line_width=2,
            marker_color="rgba(0, 48, 73,0.7)",
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

    @staticmethod
    def rolling_purity_performance(sales: pd.DataFrame, item="None"):
        sales = sales if item == "None" else sales[sales["Item Category"] == item]

        def add_line(fig, purity: str, color):
            """Adds a line for a given purity."""
            df = Analytics.segment_performance(sales, purity)
            fig.add_trace(
                go.Scatter(
                    x=df["Day"],
                    y=df["RollingAvg"],
                    name=purity,
                    line=dict(color=color, width=2),
                )
            )

        # Plot for all three as lines
        fig = go.Figure()
        add_line(fig, "18K", Color.K18.value)
        add_line(fig, "22K", Color.K22.value)
        add_line(fig, "21K", Color.K21.value)

        fig.update_traces(mode="lines", marker=dict(symbol="circle", size=8))
        fig.update_layout(
            xaxis_title="Day",
            yaxis_title="Making Value",
            legend=dict(x=0.99, y=0.99),
            template="plotly_white",
            height=600,
            width=1000,
        )
        return fig

    @staticmethod
    def item_mc_heatmap(sales: pd.DataFrame, purity, normalize=False) -> None:
        """
        Generates a heatmap of item making charges by item category and purity.

        Args:
            sales (pd.DataFrame): DataFrame containing sales data.
        """

        # ----- Isolate target data ----- #
        df = (
            sales.copy()
            if purity == "None"
            else sales[sales["Purity Category"] == purity].copy()
        )

        df = (
            df.groupby(["Item Category", "Weight Range"])
            .agg({"Making Value": "sum"})
            .reset_index()
        )

        # Min-Max Normalized Values for each Item Category
        df["Value_norm"] = df.groupby("Item Category")["Making Value"].transform(
            lambda x: (x - x.min()) / (x.max() - x.min())
        )

        # Calculate zmax
        top = df.sort_values("Making Value", ascending=False)["Making Value"]
        a, b = top.iloc[0], top.iloc[1] if len(top) > 1 else (top.iloc[0], 0)
        weight = 10
        zmax = (a + (weight * b)) / (weight + 1)

        # Variable for normalization
        value = "Value_norm" if normalize else "Making Value"
        color_label = "Frequency" if normalize else "Making Value"
        zmax = df[value].max() if normalize else zmax

        # Plot
        fig = px.imshow(
            df.pivot(index="Item Category", columns="Weight Range", values=value),
            labels=dict(x="Item Weight", y="Item Category", color=color_label),
            # zmax=df.sort_values(" Making Value ", ascending=False).iloc[1][" Making Value "],
            zmax=zmax,
            color_continuous_scale=px.colors.sequential.Plasma,
        )
        fig.update_xaxes(side="bottom")

        # Make axes labels and ticks bold and larger
        fig.update_xaxes(title_font=dict(size=14), tickfont=dict(size=12))
        fig.update_yaxes(title_font=dict(size=14), tickfont=dict(size=12))

        fig.update_layout(
            height=600,
            width=1000,
            template="plotly_white",
        )

        return fig
