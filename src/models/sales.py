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
        "22K": (0.9165, 0.926),
        "21K": (0.875, 0.880),
        "18K": (0.75, 0.76),
        "9K": (0.375, 0.4),
    }

    @staticmethod
    def get_purity_category(purity: float):
        for key, spread in Purity.ranges.items():
            if purity >= spread[0] and purity <= spread[1]:
                return key
        return ValueError(f"No compatible purity found for {purity}.")

    @staticmethod
    def get_manufacturing_purity(purity: float):
        for key, spread in Purity.ranges.items():
            if purity >= spread[0] and purity <= spread[1]:
                return spread[0]
        return ValueError(f"No compatible purity found for {purity}.")


class Sales:
    """
    Integrated sales data from multiple sources.
    """

    def __init__(self, df: pd.DataFrame = None):
        self._df: pd.DataFrame = df

    @property
    def data(self):
        return self._df

    def add_data(self, df: pd.DataFrame):
        """
        Adds data to the `_df` attribute.

        Args:
            df (pd.DataFrame): The dataframe to add.
        """
        df = self.__preprocess(df)
        if self._df is None:
            self._df = df
        else:
            self._df = pd.concat([self._df, df], ignore_index=True)

    def __preprocess(self, df):
        # Date Attributes
        df["Month"] = df["DocDate"].dt.to_period("M").astype(str)
        df["Week"] = df["DocDate"].dt.to_period("W").astype(str)
        df["Day"] = df["DocDate"].dt.to_period("D").astype(str)

        # Codes and Categories
        df["ItemCode"] = df["ItemCode"].str.upper()
        df["ItemCategory"] = df["ItemCode"].str.extract(r"\d{2}(\w+)")
        df["ItemCategory"] = df["ItemCategory"].map(
            {
                "BRA": "Bracelets",
                "CHA": "Chains",
                "BAN": "Bangles",
                "RIN": "Rings",
                "PEN": "Pendants",
            }
        )

        # Purity
        df["PurityCategory"] = df["Purity"].apply(Purity.get_purity_category)
        df["ManufacturingPurity"] = df["Purity"].apply(Purity.get_manufacturing_purity)

        # Calculate gold earnings
        df["GoldGains"] = (df.Purity - df.ManufacturingPurity) * df.GrossWt

        df["ItemWeight"] = df["GrossWt"] / df["QtyInPcs"]

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
        df["WeightRange"] = pd.cut(
            df["ItemWeight"], bins=bins, labels=labels, right=False
        )

        return df
