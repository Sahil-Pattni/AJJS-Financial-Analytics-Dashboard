"""
@author: Sahil Pattni

This is the super-class for all sales data.
Sales data must have the following columns:

    DocNumber (str): The invoice or record number.
    DocDate (pd.datetime): The date (and optionally) time of the transaction.
    TaCode (str): The customer's UID
    TAName (str): The full name for the customer.
    ItemCode (str): The item's code (e.g. `18BRA`)
    GrossWt (float): The gross weight of the items sold.
    PureWt (float): The equivalent pure weight of the items sold.
    Purity (float): The purity (in per-thousands) of the items sold.
    MakingRt (float): The making rate per gram of the items sold.
    MakingValue (float): The total making charges for the items sold.

The following columns will be auto-generated
    TransactionType (str): The transaction classification.
    ItemCategory (str): The type of jewellery (e.g. Bracelets, Chains, ...)
    PurityCategory (str): The purity of the jewellery (e.g. `22K`)
    QtyInPcs (int): The number of units sold.
    ItemWeight (float): The average per-item weight.
    WtRange (float): The weight range of the items
    Month (str): The month of the transaction.
    Week (str): The week of the transaction.
    Day (str): The day of the transaction.
"""

from typing import List
from enum import Enum
import pandas as pd
import subprocess
import logging
import os
import io
import re


class Purity:
    ranges = {
        "22K": (0.916, 0.926),
        "21K": (0.875, 0.880),
        "18K": (0.75, 0.76),
        "9K": (0.375, 0.41),
    }

    @staticmethod
    def get_purity_category(purity: float):
        for key, spread in Purity.ranges.items():
            if purity >= spread[0] and purity <= spread[1]:
                return key
        raise ValueError(f"No compatible purity found for {purity}.")

    @staticmethod
    def get_manufacturing_purity(purity: float):
        for key, spread in Purity.ranges.items():
            if purity >= spread[0] and purity <= spread[1]:
                return spread[0]
        raise ValueError(f"No compatible purity found for {purity}.")


class Sales:
    """
    Integrated sales data from multiple sources.
    """

    required_columns = [
        "Invoice Number",
        "Date",
        "Customer",
        "Item Code",
        "Purity",
        "Unit Quantity",
        "Gross Weight",
        "Pure Weight",
        "Making Rate",
        "Making Value",
    ]

    def __init__(self, df: pd.DataFrame = None):
        self._df: pd.DataFrame = df

    @property
    def data(self):
        return self._df

    @property
    def column_names(self) -> List[str]:
        """
        Returns the list of required columns in the sales data.
        """
        return Sales.required_columns

    def add_data(self, df: pd.DataFrame, mapping: dict = None):
        """
        Adds data to the `_df` attribute.

        Args:
            df (pd.DataFrame): The dataframe to add.
            mapping (dict): A dictionary of column name mapping.
        """
        if mapping:
            if not all(k in Sales.required_columns for k in mapping.values()):
                raise ValueError(
                    "Not all required keys in mapping are present in the dataframe."
                )
            df = df.rename(columns=mapping)
        df = self.__preprocess(df)
        if self._df is None:
            self._df = df
        else:
            self._df = pd.concat([self._df, df], ignore_index=True)

    def __preprocess(self, df):
        # Date Attributes
        df["Month"] = df["Date"].dt.to_period("M").astype(str)
        df["Week"] = df["Date"].dt.to_period("W").astype(str)
        df["Day"] = df["Date"].dt.to_period("D").astype(str)

        # Codes and Categories
        df["Item Code"] = df["Item Code"].str.upper()
        df["Item Category"] = df["Item Code"].str.extract(r"\d{0,2}(\w+)")
        df["Item Category"] = df["Item Category"].map(
            {
                "BRA": "Bracelets",
                "CHA": "Chains",
                "C": "Chains",
                "CHAHA": "Chains",
                "BAN": "Bangles",
                "RIN": "Rings",
                "RING": "Rings",
                "PEN": "Pendants",
                "PSET": "Pendants",
                "UNCAT": "Uncategorized",
                "UNK": "Uncategorized",
            }
        )

        # Remove Uncategorized items if none exist
        if df[df["Item Category"] == "Uncategorized"].empty:
            df = df[df["Item Category"] != "Uncategorized"].copy()

        # Edge case: Drop 0.995
        df = df[df["Purity"] != 0.995].copy()

        # Purity
        df["Purity Category"] = df["Purity"].apply(Purity.get_purity_category)
        df["Manufacturing Purity"] = df["Purity"].apply(Purity.get_manufacturing_purity)

        # Calculate gold earnings
        df["Gold Gains"] = (df["Purity"] - df["Manufacturing Purity"]) * df[
            "Gross Weight"
        ]

        df["Item Weight"] = df["Gross Weight"] / df["Unit Quantity"]

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
        df["Weight Range"] = pd.cut(
            df["Item Weight"], bins=bins, labels=labels, right=False
        )

        return df
