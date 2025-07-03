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
    def generate_sales_analytics(df: pd.DataFrame):

        with st.sidebar.container(border=True):
            st.subheader("Item Weight Distribution")
            item = st.selectbox(
                "Select Item",
                df["ItemCategory"].unique(),
                index=0,
                help="Select an item to view its weight distribution.",
            )
            purity = st.selectbox(
                "Select Purity",
                ["None"] + df["PurityCategory"].unique().tolist(),
                index=0,
                help="Select a purity category to filter the weight distribution.",
            )
            nbins = st.slider(
                "Number of Bins",
                min_value=10,
                value=50,
                step=5,
                help="Select the number of bins for the histogram.",
            )

        st.subheader("Making Charges Purity Distribution")
        q, k = st.columns([1, 1])
        with q:
            fig = Plots.monthwise_sales_by_purity(Analytics.monthly_sales_data(df))
            st.plotly_chart(fig, use_container_width=True)

        with k:
            fig = Plots.sales_sunburst(Analytics.sales_item_sunburst_data(df))
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Weekly Sales Analysis")
        q, k = st.columns([1, 1])
        with q:
            fig = Plots.weekly_monthly_boxplot(df)
            st.plotly_chart(fig, use_container_width=True)
        with k:
            fig = Plots.sales_histogram(df)
            st.plotly_chart(fig, use_container_width=True)

        q, k = st.columns([1, 1])
        with k:
            fig = Plots.item_weight_boxplot(
                df, item_category=item, purity=None if purity == "None" else purity
            )
            st.plotly_chart(fig, use_container_width=True)
        with q:
            fig = Plots.item_weight_distribution(
                df,
                item_category=item,
                nbins=nbins,
                purity=None if purity == "None" else purity,
            )
            st.plotly_chart(fig, use_container_width=True)

        x, y = st.columns(2)
        with x:
            st.subheader("Making Rate by Item")
            st.dataframe(Components.sales_agg(df, "ItemCode"), use_container_width=True)

        with y:
            st.subheader("Making Rate by Purity")
            st.dataframe(
                Components.sales_agg(df, "PurityCategory"), use_container_width=True
            )
