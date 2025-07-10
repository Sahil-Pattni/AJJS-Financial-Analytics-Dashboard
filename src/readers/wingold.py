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
                "NetAmount",
                "PurityDiff",
                "TaxAmount",
            ]
        ]

        # Set transaction type
        self._transactions["TransactionType"] = self._transactions["DocNumber"].apply(
            self.__get_transaction_type
        )

        # Datetime conversions
        self._transactions["DocDate"] = self._transactions["DocDate"].str.replace(
            "0001", "1971"
        )
        self._transactions["DocDate"] = pd.to_datetime(self._transactions["DocDate"])
        self._transactions["Month"] = (
            self._transactions["DocDate"].dt.to_period("M").astype(str)
        )
        self._transactions["Week"] = (
            self._transactions["DocDate"].dt.to_period("W").astype(str)
        )
        self._transactions["Day"] = (
            self._transactions["DocDate"].dt.to_period("D").astype(str)
        )
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

        # Codes and Categories
        self._transactions["ItemCode"] = self._transactions["ItemCode"].str.upper()
        self._transactions["ItemCategory"] = self._transactions["ItemCode"].str.extract(
            r"\d{2}(\w+)"
        )
        self._transactions["ItemCategory"] = self._transactions["ItemCategory"].map(
            {
                "BRA": "Bracelets",
                "CHA": "Chains",
                "BAN": "Bangles",
                "RIN": "Rings",
                "PEN": "Pendants",
            }
        )

        # Purity
        self._transactions["PurityCategory"] = self._transactions["Purity"].apply(
            self.__get_purity_category
        )
        self._transactions["ManufacturingPurity"] = self._transactions["Purity"].apply(
            self.__get_purity_manufacturing
        )

        self._transactions["ItemWeight"] = (
            self._transactions["GrossWt"] / self._transactions["QtyInPcs"]
        )

        # Weight Ranges
        bins = [0, 20, 30, 40, 50, 100, 150, float("inf")]
        labels = [
            "<20g",
            "20-30g",
            "30-40g",
            "40-50g",
            "50-100g",
            "100-150g",
            ">150g",
        ]
        self._transactions["WeightRange"] = pd.cut(
            self._transactions["ItemWeight"], bins=bins, labels=labels, right=False
        )

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
        sales["GoldGains"] = (sales.Purity - sales.ManufacturingPurity) * sales.GrossWt

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

    def __get_purity_category(self, purity) -> str:
        """
        Tag purity levels based on the purity.
        """
        purity = float(purity)
        if purity >= 0.92 and purity <= 0.926:
            return "22K"
        elif purity >= 0.875 and purity <= 0.880:
            return "21K"
        elif purity >= 0.750 and purity <= 0.760:
            return "18K"
        elif purity >= 0.375 and purity <= 0.40:  # TODO: Verify upper bound
            return "9K"

    def __get_purity_manufacturing(self, purity) -> str:
        """
        Tag purity levels based on the purity.
        """
        purity = float(purity)
        if purity >= 0.9165 and purity <= 0.926:
            return 0.9165
        elif purity >= 0.875 and purity <= 0.880:
            return 0.875
        elif purity >= 0.750 and purity <= 0.760:
            return 0.750
        elif purity >= 0.375 and purity <= 0.40:  # TODO: Verify upper bound
            return 0.375

    def __fix_capitalization(self, name: str):
        """
        Fixes the capitalization of a name by capitalizing the first letter of each word.
        """
        if "V I V A A" in name:
            name = name.replace("V I V A A", "Vivaa")
        name = " ".join(word.capitalize() for word in name.split())
        name = re.sub(r"[Ll]\.?[Ll]\.?[Cc]", "LLC", name)
        return name

    def __get_transaction_type(self, doc_number: str):
        """
        Determines the transaction category based on the document number.

        Args:
            doc_number (str): The document number to classify.

        Returns:
            str: The type of transaction.
        """
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
