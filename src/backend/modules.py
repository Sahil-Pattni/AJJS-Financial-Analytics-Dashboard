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
            .agg({"GrossWt": "sum", "PureWt": "sum", "MakingValue": "sum"})
            .sort_values(by="MakingValue", ascending=False)
            .style.format(
                {
                    "GrossWt": "{:,.2f} g",
                    "PureWt": "{:,.2f} g",
                    "MakingValue": "{:,.2f} AED",
                }
            )
        )

    @staticmethod
    def generate_sales_analytics(df: pd.DataFrame):
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

        _, q, _ = st.columns([1, 5, 1])
        with q:
            with st.sidebar.container(border=True):
                st.subheader("Item Weight Distribution")
                item = st.selectbox(
                    "Select Item",
                    df["ItemCategory"].unique(),
                    index=0,
                    help="Select an item to view its weight distribution.",
                )
            fig = Plots.item_weight_distribution(df, item_category=item)
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
