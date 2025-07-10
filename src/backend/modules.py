import streamlit as st
from streamlit import session_state as ss
import pandas as pd
from src.backend.analytics import Analytics
from src.backend.plots import Plots
import plotly.express as px


class Components:
    @staticmethod
    def sales_agg(df: pd.DataFrame, colname: str):
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
    def sidebar_settings(df: pd.DataFrame):
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
    def generate_sales_page(df: pd.DataFrame):
        # Generate the settings
        Components.sidebar_settings(df)

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

            # Section 2.2: Making Rate Breakdown
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
