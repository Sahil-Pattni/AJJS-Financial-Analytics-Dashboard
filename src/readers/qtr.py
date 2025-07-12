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

    def _read_qtr_file(self, workbook, sheet_name: str) -> pd.DataFrame:
        df = pd.read_excel(
            workbook,
            sheet_name=sheet_name,
            header=1,
            usecols="A:F",
            dtype={
                "Date": "datetime64[ns]",
                "Account": "str",
                "Voucher": "str",
                "Weight": "float64",
                "Pure": "float64",
                "M-Charge": "float64",
            },
        )
        # Remove first row
        df = df.iloc[1:].copy()
        df["Weight"] = df["Weight"].fillna(0)
        df["Pure"] = df["Pure"].fillna(0)
        df["M-Charge"] = df["M-Charge"].fillna(0)

        # Derived rows
        df["Purity"] = round(df["Pure"] / df["Weight"], 3)
        df["Making Rate"] = round(df["M-Charge"] / df["Weight"], 2)
        df["Item Code"] = pd.NA
        df["Unit Quantity"] = 1
        df["Transaction Type"] = "SALE"

        # Edge case: Rename customers
        df["Account"].replace(
            {
                "VIVAA": "Vivaa Jewellery Trading LLC",
                "VIVAA S": "Vivaa Jewellery Trading LLC",
            },
            inplace=True,
        )

        return df[pd.notna(df["Date"])]

    def _decrypt_workbook(self, filepath: str, password: str) -> io.BytesIO:
        decrypted_workbook = io.BytesIO()
        with open(filepath, "rb") as file:
            office_file = msoffcrypto.OfficeFile(file)
            office_file.load_key(password=password)
            office_file.decrypt(decrypted_workbook)
        return decrypted_workbook
