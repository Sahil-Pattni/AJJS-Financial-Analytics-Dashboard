from datetime import datetime
import pandas as pd
from src.readers.cashbook import CashbookReader


class Analytics:

    @staticmethod
    def income_expenses_data(
        sales_df: pd.DataFrame,
        cashbook: pd.DataFrame,
        fixed_costs: pd.DataFrame,
        gold_rate: float = 390.0,
    ) -> pd.DataFrame:
        """
        Combine sales and cashbook data into a single DataFrame.

        Args:
            sales_df (pd.DataFrame): DataFrame containing sales data.
            cashbook (pd.DataFrame): DataFrame containing cashbook data.
            fixed_costs (pd.DataFrame): DataFrame containing fixed costs data.
            gold_rate (float): The current gold rate in AED per gram. Defaults to 390.0.

        Returns:
            pd.DataFrame: Combined DataFrame with income and expenses.
        """
        # ----- Transform the data ----- #
        # Legitimate sales data
        monthly_making = (
            sales_df.groupby(sales_df.DocDate.dt.to_period("M"))
            .agg(
                {
                    "MakingValue": "sum",
                    "GoldGains": "sum",
                }
            )
            .reset_index()
        )
        monthly_making.columns = ["Month", "Making Charges", "GoldGains"]
        monthly_making["GoldGains"] = monthly_making["GoldGains"] * gold_rate
        monthly_making["Month"] = monthly_making["Month"].dt.to_timestamp()

        # QTR sales data
        monthly_qtr_making = (
            cashbook[cashbook["Sub-Category"] == "QTR Making Charges"]
            .groupby(cashbook.Date.dt.to_period("M"))["Credit"]
            .sum()
            .reset_index()
        )
        monthly_qtr_making.columns = ["Month", "QTR Making Charges"]
        monthly_qtr_making["Month"] = monthly_qtr_making["Month"].dt.to_timestamp()

        # Expenses
        # We exclude employees and rent from expenses as they're accounted
        # for in fixed costs.
        monthly_expenses = (
            cashbook[(cashbook.Debit > 0) & (cashbook["Cost Type"] != "FIXED")]
            .groupby(cashbook.Date.dt.to_period("M"))["Debit"]
            .sum()
            .reset_index()
        )
        monthly_expenses.columns = ["Month", "Expenses"]
        monthly_expenses["Month"] = monthly_expenses["Month"].dt.to_timestamp()

        # Static fixed costs
        fixed_costs = fixed_costs.copy()
        fc = fixed_costs["Debit"].sum() / 12
        # Fixed costs from cashbook
        cbfixed = (
            cashbook[
                (cashbook["Cost Type"] == "FIXED")
                & (cashbook["Sub-Category"] != "Staff Salaries")
                & (cashbook["Sub-Category"] != "Visa Fees")
                & (cashbook["Sub-Category"] != "Loans")
                & (cashbook["Super-Category"] != "Rent")
            ]["Debit"].sum()
            / 12
        )

        # ----- Merge the data ----- #
        monthly_data = pd.merge(
            monthly_making, monthly_qtr_making, on="Month", how="outer"
        )
        monthly_data = pd.merge(monthly_data, monthly_expenses, on="Month", how="outer")

        monthly_data["Fixed Costs"] = fc + cbfixed
        monthly_data.fillna(0, inplace=True)

        # Add derived columns
        monthly_data["Total Income"] = (
            monthly_data["Making Charges"] + monthly_data["QTR Making Charges"]
        )

        # Convert to negative for expenses
        monthly_data["Total Cost"] = -1 * (
            monthly_data["Expenses"] + monthly_data["Fixed Costs"]
        )

        monthly_data["Net Profit"] = (
            monthly_data["Total Income"] + monthly_data["Total Cost"]
        )

        monthly_data["Position"] = monthly_data["Net Profit"].apply(
            lambda x: "Profit" if x > 0 else "Loss"
        )
        monthly_data.set_index("Month", inplace=True)

        return monthly_data

    @staticmethod
    def fixed_cost_pie_chart_data(cashbookReader: CashbookReader) -> pd.DataFrame:
        """
        Generates pie chart data of the expense categories.
        """
        cashbook = cashbookReader.cashbook
        # Exclude rent and salaries
        expenses = (
            cashbook[
                (cashbook.Debit > 0)
                & (cashbook["Cost Type"] == "FIXED")
                & (cashbook["Sub-Category"] != "Staff Salaries")
                & (cashbook["Sub-Category"] != "Visa Fees")
                & (cashbook["Sub-Category"] != "Loans")
                & (cashbook["Super-Category"] != "Rent")
            ]
            .groupby(["Super-Category", "Sub-Category", "Cost Type"])
            .aggregate({"Debit": "sum"})
            .reset_index()
        )

        # Derive fixed costs up until the current month
        fc = cashbookReader.fixed_costs.copy()
        fc["Debit"] = fc["Debit"] / 12

        expenses["Debit"] = expenses["Debit"] / 12

        #  Combine cashbook expenses and fixed costs
        expenses = pd.concat([expenses, fc], ignore_index=True)

        expenses.sort_values(by=["Cost Type", "Debit"], ascending=False, inplace=True)

        return expenses

    @staticmethod
    def variable_cost_pie_chart_data(cashbookReader: CashbookReader) -> pd.DataFrame:
        """
        Generates pie chart data of the expense categories.
        """
        cashbook = cashbookReader.cashbook
        cashbook = cashbook[cashbook["Cost Type"] == "VARIABLE"].copy()

        cashbook.sort_values(by=["Cost Type", "Debit"], ascending=False, inplace=True)

        return cashbook

    @staticmethod
    def monthly_sales_data(df: pd.DataFrame):
        df = df.groupby(["Month", "PurityCategory"]).agg(
            {"GrossWt": "sum", "PureWt": "sum", "MakingValue": "sum"}
        )

        df.reset_index(inplace=True)

        return df

    @staticmethod
    def sales_item_sunburst_data(
        df: pd.DataFrame, on: str = "MakingValue"
    ) -> pd.DataFrame:
        """
        Generate a DataFrame for sunburst chart data by item.

        Args:
            sales_df (pd.DataFrame): DataFrame containing sales data.

        Returns:
            pd.DataFrame: DataFrame with sales data for sunburst chart.
        """
        # ----- Transform the data ----- #
        df = (
            df.groupby(["PurityCategory", "ItemCategory", "ItemCode"])
            .agg(
                {
                    "GrossWt": "sum",
                    "PureWt": "sum",
                    "MakingValue": "sum",
                }
            )
            .sort_values(by="MakingValue", ascending=False)
            .reset_index()
        )
        df["MakingRt"] = df["MakingValue"] / df["GrossWt"]
        df = df[df.GrossWt > 0]
        return df

    @staticmethod
    def segment_performance(sales, category):
        """
        Generate a 3 week rolling average of making value and gross weight
        for a given purity category.
        """
        df = (
            sales[sales.PurityCategory == category]
            .groupby("Day")
            .agg({"MakingValue": "sum", "GrossWt": "sum"})
            .reset_index()
            .sort_values(by="Day", ascending=True)
        )
        df["RollingAvg"] = df["MakingValue"].rolling(window=21, min_periods=1).mean()

        return df
