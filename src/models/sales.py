from typing import List
from enum import Enum
import pandas as pd
import subprocess
import logging
import os
import io
import re


class Sales:
    def __init__(self, df: pd.DataFrame = None):
        self._df: pd.DataFrame = df

    @property
    def data(self):
        return self._df

    def add_data(self, df: pd.DataFrame):
        if self._df is None:
            self._df = df
        else:
            self._df = pd.concat([self._df, df], ignore_index=True)
