import streamlit as st
from streamlit import session_state as ss
import pandas as pd
from src.backend.analytics import Analytics
from src.backend.plots import Plots
import plotly.express as px
from datetime import datetime


class Components:
    @staticmethod
    def sales_agg(df: pd.DataFrame, colname: str) -> pd.DataFrame:
        """
        Generate a summary DataFrame for sales aggregation based on the specified column name.

        Args:
            df (pd.DataFrame): The DataFrame containing sales data.
            colname (str): The column name to group by for aggregation.

        Returns:
            pd.DataFrame: A styled DataFrame with aggregated sales data.
        """
        return (
            df.groupby(colname)
            .agg(
                {
                    "GrossWt": "sum",
                    "PureWt": "sum",
                    "MakingRt": "mean",
                    "MakingValue": "sum",
                }
            )
            .sort_values(by="MakingValue", ascending=False)
            # Rename cols
            .rename(
                columns={
                    "GrossWt": "Gross Weight",
                    "PureWt": "Pure Weight",
                    "MakingRt": "Making Rate",
                    "MakingValue": "Making Value",
                }
            )
            .style.format(
                {
                    "Gross Weight": "{:,.2f} g",
                    "Pure Weight": "{:,.2f} g",
                    "Making Rate": "{:,.2f} AED/g",
                    "Making Value": "{:,.2f} AED",
                }
            )
        )

    @staticmethod
    def sidebar_settings(df: pd.DataFrame) -> None:
        """
        Generate sidebar settings for the sales analytics page.
        """
        with st.sidebar.container(border=True):
            st.subheader("Item Weight Distribution")
            st.selectbox(
                "Select Item",
                df["ItemCategory"].unique().tolist() + ["None"],
                index=0,
                key="item",
                help="Select an item to view its weight distribution.",
            )

            st.selectbox(
                "Select Purity",
                ["None"] + df["PurityCategory"].unique().tolist(),
                index=0,
                key="purity",
                help="Select a purity category to filter the weight distribution.",
            )
            st.slider(
                "Number of Bins",
                min_value=10,
                value=50,
                step=5,
                key="nbins",
                help="Select the number of bins for the histogram.",
            )

            st.toggle(
                "Normalize Histogram",
                value=False,
                key="normalize",
                help="Check to normalize the histogram to show percentages.",
            )

    @staticmethod
    def __monthly_metric(df: pd.DataFrame, col: str, unit: str) -> None:
        """
        Generate a monthly metric for the specified column.

        Args:
            df (pd.DataFrame): The DataFrame containing sales data.
            col (str): The column name to calculate the monthly metric for.
        """
        monthly = df.groupby("Month").agg({col: "sum"})
        # Exclude current month if it is not complete
        if datetime.now().strftime("%Y-%m") == monthly.index[-1]:
            monthly = monthly[:-1]
        prev_monthly = monthly[:-1].copy()
        current = monthly[col].mean()
        prev = prev_monthly[col].mean()
        st.metric(
            f"Average Monthly {col.replace('MakingValue', 'Revenue')}",
            f"{monthly[col].mean():,.2f} {unit}",
            delta=f"{((current - prev) * 100)/current:.2f}%",
            border=True,
        )

    @staticmethod
    def generate_sales_page(df: pd.DataFrame) -> None:
        """
        Generate the sales page components.

        Args:
            df (pd.DataFrame): The DataFrame containing sales data.
        """
        # Generate the settings
        Components.sidebar_settings(df)

        # Section 0: Key Metrics
        with st.container(border=True):
            st.header("Key Metrics")
            a, b, c = st.columns(3)
            with a:
                Components.__monthly_metric(df, "GrossWt", "g")
            with b:
                Components.__monthly_metric(df, "MakingValue", "AED")
            with c:
                driver = (
                    df.groupby("ItemCategory")
                    .agg({"GrossWt": "sum", "MakingValue": "sum"})
                    .sort_values(by="MakingValue", ascending=False)
                    .reset_index()
                ).iloc[0]
                st.metric(
                    "Top Driver",
                    f"{driver['ItemCategory']}",
                    delta=f"{driver['MakingValue']:,.2f} AED --- {driver['GrossWt']:,.2f} g",
                    border=True,
                )

        # Section 1: Volume
        with st.container(border=True):
            st.header("Volume Analysis")

            # Section 1.1: Monthly Sales & Breakdown
            q, k = st.columns([1, 1])
            with q:
                fig2 = Plots.monthwise_sales(
                    Analytics.monthly_sales_data(df), y="GrossWt"
                )
                st.plotly_chart(fig2, use_container_width=True, key="mg")
            with k:
                fig3 = Plots.sales_sunburst(
                    Analytics.sales_item_sunburst_data(df, on="GrossWt"), y="GrossWt"
                )
                st.plotly_chart(fig3, use_container_width=True, key="sg")

            # Section 1.2: Weekly Volume
            q, k = st.columns([1, 1])
            with q:
                fig = Plots.sales_histogram(df)
                st.plotly_chart(fig, use_container_width=True)

            with k:
                kwargs = {
                    "item_category": (
                        ss.item if ss.get("item", None) != "None" else None
                    ),
                    "purity": ss.purity if ss.get("purity", None) != "None" else None,
                }
                fig = Plots.item_weight_distribution(
                    df,
                    nbins=ss.nbins,
                    normalize=ss.normalize,
                    **kwargs,
                )
                st.plotly_chart(fig, use_container_width=True)

        # Section 2: Revenue
        with st.container(border=True):
            st.header("Revenue Analysis")

            # Section 2.1:  Monthly sales & breakdown
            q, k = st.columns([1, 1])
            with q:
                fig = Plots.monthwise_sales(Analytics.monthly_sales_data(df))
                st.plotly_chart(fig, use_container_width=True)
            with k:
                fig = Plots.sales_sunburst(Analytics.sales_item_sunburst_data(df))
                st.plotly_chart(fig, use_container_width=True)

            # Section 2.2: Item Making Charges Heatmap and Rolling Purity Performance
            a, b = st.columns(2)
            with a:
                with st.container(border=True):
                    st.header("Weight Range Profitability")
                    x, y = st.columns([2, 1])
                    with x:
                        st.selectbox(
                            "Select Purity",
                            ["None"] + df["PurityCategory"].unique().tolist(),
                            index=0,
                            key="purity_heatmap",
                        )
                    with y:
                        st.toggle(
                            "Normalize Heatmap",
                            value=False,
                            key="normalize_heatmap",
                            help="Normalize to show frequency by item category",
                        )
                    fig = Plots.item_mc_heatmap(
                        df, purity=ss.purity_heatmap, normalize=ss.normalize_heatmap
                    )
                    st.plotly_chart(fig, use_container_width=True)
            with b:
                with st.container(border=True):
                    st.header("3-Week Rolling Average: Revenue")
                    st.selectbox(
                        "Select Item",
                        ["None"] + df["ItemCategory"].unique().tolist(),
                        index=0,
                        key="item_rolling",
                    )
                    # Section 2.3: Rolling Purity Performance
                    fig = Plots.rolling_purity_performance(df, item=ss.item_rolling)
                    st.plotly_chart(fig, use_container_width=True)

            # Section 2.3: Making Rate Breakdown
            x, y = st.columns(2)
            with x:
                st.subheader("Making Rate by Item")
                st.dataframe(
                    Components.sales_agg(df, "ItemCode"), use_container_width=True
                )

            with y:
                st.subheader("Making Rate by Purity")
                st.dataframe(
                    Components.sales_agg(df, "PurityCategory"), use_container_width=True
                )
