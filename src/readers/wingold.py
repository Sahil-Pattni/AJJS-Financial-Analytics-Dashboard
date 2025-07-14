from typing import List
from enum import Enum
import pandas as pd
import subprocess
import logging
import os
import io
import re


class TransactionType(Enum):
    SALE = 1
    PURCHASE = 2
    RETURN = 3
    DIRECT_SALE = 4

    def identify_transaction(doc_number: str):
        if doc_number.startswith("S"):
            return TransactionType.SALE.name
        elif doc_number.startswith("P"):
            return TransactionType.PURCHASE.name
        elif doc_number.startswith("R"):
            return TransactionType.RETURN.name
        elif doc_number.startswith("D"):
            return TransactionType.DIRECT_SALE.name
        else:
            return "Unknown"


class WingoldReader:
    def __init__(self, filepath: str):
        """
        Initializes the WingoldReader with the path to the Wingold database file.

        Args:
            filepath (str): Path to the Wingold .mdb file.
        """
        # Set up tables
        self._transactions = self.__read_table(filepath, "BinCard")
        self._accounts = self.__read_table(filepath, "Party")
        self.__preprocess()
        self._sales = self.__extract_sales()

    @property
    def transactions(self) -> pd.DataFrame:
        """
        Returns the transactions DataFrame.
        """
        return self._transactions

    @property
    def sales(self) -> pd.DataFrame:
        """
        Returns the sales DataFrame.
        """
        return self._sales

    def __preprocess(self) -> None:
        """
        Preprocesses the transactions DataFrame to clean and format the data.
        """
        logging.info("Preprocessing transactions...")
        # Keep only required columns
        self._transactions = self._transactions[
            [
                "DocNumber",
                "DocDate",
                "TaCode",
                "ItemCode",
                "Purity",
                "QtyInPcs",
                "GrossWt",
                "PureWt",
                "MakingRt",
                "MakingValue",
            ]
        ]

        # Set transaction type
        self._transactions["TransactionType"] = self._transactions["DocNumber"].apply(
            TransactionType.identify_transaction
        )

        # Datetime conversions
        self._transactions["DocDate"] = self._transactions["DocDate"].str.replace(
            "0001", "1971"
        )
        self._transactions["DocDate"] = pd.to_datetime(self._transactions["DocDate"])
        self._transactions.sort_values(by="DocDate", inplace=True)

        # Add name from accounts
        self._accounts.rename(
            columns={"TACode": "TaCode"}, inplace=True
        )  # Keep key column uniform
        self._accounts["TAName"] = self._accounts["TAName"].apply(
            self.__fix_capitalization
        )
        accounts_map = self._accounts.set_index("TaCode")["TAName"].to_dict()
        self._transactions["TAName"] = self._transactions["TaCode"].map(accounts_map)

        # Mark as non-QTR
        self._transactions["QTR"] = False

    def __extract_sales(self) -> pd.DataFrame:
        """
        Extracts sales data from the transactions DataFrame, including sales returns.

        Returns:
            pd.DataFrame: A DataFrame containing sales data with returns as negative values.
        """
        # ----- Extract Sales Data ----- #
        logging.info("Extracting sales data...")
        # Convert sales returns to negative values
        sales_returns = self._transactions[
            self._transactions.DocNumber.str.startswith("R")
        ].copy()
        sales_returns["GrossWt"] = -sales_returns["GrossWt"]
        sales_returns["PureWt"] = -sales_returns["PureWt"]
        sales_returns["MakingValue"] = -sales_returns["MakingValue"]

        # Get sales
        sales = self._transactions[
            self._transactions.DocNumber.str.startswith("S")
        ].copy()
        # Merge with negative sales returns values
        sales = pd.concat([sales, sales_returns], ignore_index=True)

        return sales

    def __read_table(self, filepath, table_name: str) -> pd.DataFrame:
        """
        Reads a table from a Microsoft Access database file using mdb-export.

        Args:
            filepath (str): Path to the .mdb file.
            table_name (str): Name of the table to read.

        Returns:
            pd.DataFrame: DataFrame containing the table data.
        """
        logging.info(f"Reading table '{table_name}'")
        data = subprocess.check_output(["mdb-export", filepath, table_name])
        return pd.read_csv(io.BytesIO(data))

    def __fix_capitalization(self, name: str):
        """
        Fixes the capitalization of a name by capitalizing the first letter of each word.
        """
        if "V I V A A" in name:
            name = name.replace("V I V A A", "Vivaa")
        name = " ".join(word.capitalize() for word in name.split())
        name = re.sub(r"[Ll]\.?[Ll]\.?[Cc]", "LLC", name)
        return name
