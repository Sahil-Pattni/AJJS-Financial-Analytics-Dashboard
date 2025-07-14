from dotenv import load_dotenv
from typing import List
import pandas as pd
import msoffcrypto
import json
import os
import io

load_dotenv()


class QTRReader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.password = os.getenv("QTRPassword")
        self._data = self._read_qtr_file(
            workbook=self._decrypt_workbook(filepath, self.password),
            sheet_name="Issued Record",
        )

    @property
    def data(self) -> pd.DataFrame:
        """Returns the QTR data as a pandas DataFrame."""
        return self._data

    def read_items(self, workbook, sheet_name: str = "ItemSales") -> pd.DataFrame:
        df = pd.read_excel(
            workbook,
            sheet_name=sheet_name,
            header=1,
            names=[
                "Date",
                "Customer",
                "Invoice Number",
                "Gross Weight",
                "Making Rate",
                "Making Value",
                "Item Code",
            ],
            usecols="A:G",
            dtype={
                "Date": "datetime64[ns]",
                "Customer": "str",
                "Invoice Number": "str",
                "Gross Weight": "float64",
                "Making Rate": "float64",
                "Making Value": "float64",
                "Item Code": "str",
            },
        )

        # df["Purity Category"] = df["Item Code"].str.extract(r"(\d{2}) \w+")

        # Format item code
        df["Item Code"] = (
            df["Item Code"]
            .replace(r"(\d{2}) (\w+)", r"\1\2", regex=True)
            .replace(r"CCH\w?", "CHA", regex=True)
            .replace(r"CB\w+", "BRA", regex=True)
            .replace(r"BGL", "BAN", regex=True)
            .replace("HP\w", "", regex=True)
            .replace(r"(\d{2})C", r"\1CHA", regex=True)
            .replace("PSET", "PEN", regex=False)
            .replace("SCRAP", "", regex=False)
            .replace("PURE", "", regex=False)
            .replace("", "UNK", regex=False)
        )

        return df

    def _read_qtr_file(self, workbook, sheet_name: str) -> pd.DataFrame:
        info = self.read_items(workbook)
        df = pd.read_excel(
            workbook,
            sheet_name=sheet_name,
            header=1,
            usecols="A:F",
            names=[
                "Date",
                "Customer",
                "Invoice Number",
                "Gross Weight",
                "Pure Weight",
                "Making Value",
            ],
            dtype={
                "Date": "datetime64[ns]",
                "Customer": "str",
                "Invoice Number": "str",
                "Gross Weight": "float64",
                "Pure Weight": "float64",
                "Making Value": "float64",
            },
        )
        # Remove first row
        df = df.iloc[1:].copy()
        df["Gross Weight"] = df["Gross Weight"].fillna(0)
        df["Pure Weight"] = df["Pure Weight"].fillna(0)
        df["Making Value"] = df["Making Value"].fillna(0)

        # Associated Rows
        # Add Item Code and Making Rate from info on Invoice Number
        df = df.merge(
            info[["Invoice Number", "Item Code", "Making Rate"]],
            on="Invoice Number",
            how="left",
        )

        # Derived rows
        df["Purity"] = round(df["Pure Weight"] / df["Gross Weight"], 3)
        df["Unit Quantity"] = 1
        df["Transaction Type"] = "SALE"

        # Edge case: Rename customers
        df["Customer"] = df["Customer"].replace(
            {
                "VIVAA": "Vivaa Jewellery Trading LLC",
                "VIVAA S": "Vivaa Jewellery Trading LLC",
                "NIMISHA": "Nimisha Jewellers LLC",
            },
        )

        return df[pd.notna(df["Date"])]

    def _decrypt_workbook(self, filepath: str, password: str) -> io.BytesIO:
        decrypted_workbook = io.BytesIO()
        with open(filepath, "rb") as file:
            office_file = msoffcrypto.OfficeFile(file)
            office_file.load_key(password=password)
            office_file.decrypt(decrypted_workbook)
        return decrypted_workbook
