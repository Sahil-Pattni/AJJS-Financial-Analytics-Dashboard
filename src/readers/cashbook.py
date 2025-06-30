from dotenv import load_dotenv
from typing import List
import pandas as pd
import msoffcrypto
import json
import os
import io

load_dotenv()


class CashbookReader:
    def __init__(
        self,
        filepath: str,
        expense_categories: str = "data/static/expense_categories.json",
        income_categories: str = "data/static/income_categories.json",
        fixed_costs: str = "data/static/fixed_costs.json",
        only_this_year: bool = True,
    ):
        # Read JSON files
        self.__expense_categories = self.__read_categories_file(expense_categories)
        self.__income_categories = self.__read_categories_file(income_categories)
        self.__fixed_costs = self.__read_categories_file(fixed_costs)

        # Read sheets
        workbook = self.__read_workbook(filepath)
        self._mcb, self._qtr, self._cashbook = self.__read_sheets(workbook)

        # Restrict to this year
        if only_this_year:
            current_year = pd.Timestamp.now().year
            self._cashbook = self._cashbook[
                self._cashbook["Date"].dt.year == current_year
            ]
            self._mcb = self._mcb[self._mcb["Date"].dt.year == current_year]
            self._qtr = self._qtr[self._qtr["Date"].dt.year == current_year]

        # Apply categories
        self.__assign_categories(self._cashbook)
        self.__assign_categories(self._mcb)
        self.__assign_categories(self._qtr)

        self._fixed_costs = self.__read_fixed_costs(self.__fixed_costs)

        # Re-organize columns
        col_structure = [
            "Date",
            "Details",
            "Debit",
            "Credit",
            "Balance",
            "Super-Category",
            "Sub-Category",
            "Cost Type",
            "QTR",
        ]
        self._cashbook = self._cashbook[col_structure]
        self._mcb = self._mcb[col_structure]
        self._qtr = self._qtr[col_structure]

    @property
    def cashbook(self) -> pd.DataFrame:
        """
        Returns the cashbook DataFrame.

        Returns:
            pd.DataFrame: The cashbook DataFrame.
        """
        return self._cashbook

    @property
    def fixed_costs(self) -> pd.DataFrame:
        """
        Returns the fixed costs DataFrame.

        Returns:
            pd.DataFrame: The fixed costs DataFrame.
        """
        return self._fixed_costs

    @property
    def mcb(self) -> pd.DataFrame:
        """
        Returns the main cash book DataFrame.

        Returns:
            pd.DataFrame: The main cash book DataFrame.
        """
        return self._mcb

    @property
    def qtr(self) -> pd.DataFrame:
        """
        Returns the quarterly cash book DataFrame.

        Returns:
            pd.DataFrame: The quarterly cash book DataFrame.
        """
        return self._qtr

    def __read_sheets(self, workbook) -> pd.DataFrame:
        """
        Reads the sheets from the workbook and returns a dictionary of DataFrames.

        Args:
            workbook: The decrypted workbook object.

        Returns:
            pd.DataFrame: A DataFrame containing the combined cashbook data.
        """
        mcb = self.__read_sheet(
            workbook,
            "MAIN CASH BOOK",
            ["Date", "Details", "Category", "Debit", "Credit", "Balance"],
        )
        # Set first row Credit as Balance amount
        mcb.loc[0, "Credit"] = mcb.loc[0, "Balance"]
        mcb["Balance"] = mcb.Credit.cumsum() - mcb.Debit.cumsum()
        mcb["QTR"] = False

        qtr = self.__read_sheet(
            workbook,
            "QTR CASH",
            ["Date", "Details", "Category", "Credit", "Debit", "Balance"],
        )
        qtr["Balance"] = qtr.Credit.cumsum() - qtr.Debit.cumsum()
        qtr["QTR"] = True

        cashbook = pd.concat([mcb, qtr], ignore_index=True)
        cashbook.sort_index(inplace=True)
        return mcb, qtr, cashbook

    def __read_categories_file(self, filepath):
        """
        Reads a JSON file containing categories.

        Args:
            filepath (str): Path to the JSON file.

        Returns:
            dict: Dictionary containing the categories.
        """
        with open(filepath, "r") as file:
            return json.load(file)

    def __read_workbook(self, filepath: str):
        decrypted_workbook = io.BytesIO()
        with open(filepath, "rb") as file:
            office_file = msoffcrypto.OfficeFile(file)
            office_file.load_key(password=os.getenv("ExcelPassword"))
            office_file.decrypt(decrypted_workbook)
        return decrypted_workbook

    def __read_sheet(self, workbook, sheet_name: str, cols: List[str]):
        df = pd.read_excel(
            workbook,
            sheet_name=sheet_name,
            header=2,
            names=cols,
            usecols="C:H",
            dtype={
                "Date": "datetime64[ns]",
                "Details": "string",
                "Category": "string",
                "Debit": "float64",
                "Credit": "float64",
                "Balance": "float64",
            },
        )

        df["Debit"] = df["Debit"].fillna(0)
        df["Credit"] = df["Credit"].fillna(0)
        df["Category"] = df["Category"].str.strip().str.upper()

        return df[pd.notna(df["Date"])]

    def __assign_categories(self, book):
        book["Sub-Category"] = book.apply(
            lambda row: self.__assign_subcategory(
                row,
                (
                    self.__income_categories
                    if row["Credit"] > 0
                    else self.__expense_categories
                ),
            ),
            axis=1,
        )

        book["Super-Category"] = book.apply(
            lambda row: self.__assign_supercategory(
                row,
                (
                    self.__income_categories
                    if row["Credit"] > 0
                    else self.__expense_categories
                ),
            ),
            axis=1,
        )

        # Apply cost type only on rows where Debit > 0
        book["Cost Type"] = book.apply(
            lambda row: (
                self.__assign_cost_type(row, (self.__expense_categories))
                if row["Debit"] > 0
                else ""
            ),
            axis=1,
        )

    def __read_categories_file(self, filepath):
        """
        Reads a JSON file containing categories.

        Args:
            filepath (str): Path to the JSON file.

        Returns:
            dict: Dictionary containing the categories.
        """
        with open(filepath, "r") as file:
            return json.load(file)

    def __assign_subcategory(self, row, category_db):
        """
        Assigns a subcategory to a row based on the category database.

        Args:
            row (pd.Series): A row from the DataFrame.
            category_db (dict): Dictionary containing categories and subcategories.

        Returns:
            str: The subcategory if found, otherwise "Uncategorized".
        """
        for _, subcategories in category_db.items():
            for key, vals in subcategories.items():
                if row["Category"] in vals["values"]:
                    return key
        return "Uncategorized"

    def __assign_supercategory(self, row, category_db):
        """
        Assigns a supercategory to a row based on the category database.

        Args:
            row (pd.Series): A row from the DataFrame.
            category_db (dict): Dictionary containing categories and subcategories.

        Returns:
            str: The supercategory if found, otherwise "Uncategorized".
        """
        for category, subcategories in category_db.items():
            if row["Sub-Category"] in subcategories.keys():
                return category
        return "Uncategorized"

    def __assign_cost_type(self, row, category_db):
        """
        Assigns a cost type to a row based on the category database.

        Args:
            row (pd.Series): A row from the DataFrame.
            category_db (dict): Dictionary containing categories and subcategories.

        Returns:
            str: The cost type if found, otherwise "Uncategorized".
        """
        for _, subcategories in category_db.items():
            for key, vals in subcategories.items():
                if key == row["Sub-Category"]:
                    return vals["key"]
        return "Uncategorized"

    def __read_fixed_costs(self, fixed_costs: str):
        fc = pd.DataFrame.from_dict(
            fixed_costs, orient="index", columns=["Super-Category", "Cost"]
        )
        fc.reset_index(inplace=True)
        fc.rename(columns={"index": "Sub-Category", "Cost": "Debit"}, inplace=True)
        fc["Cost Type"] = "FIXED"

        return fc
