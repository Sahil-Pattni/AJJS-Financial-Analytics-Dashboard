import io
from typing import List
import streamlit as st
from streamlit import session_state as ss
from src.readers.cashbook import CashbookReader
from src.readers.wingold import WingoldReader
from utils import present_navigation
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s\t%(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # Restricts to seconds
    force=True,
)

if "redirected" not in ss:
    ss["redirected"] = False

present_navigation()
if "cashbook" not in ss or "wingold" not in ss:
    ss["redirected"] = False
    # Go to upload page
    st.switch_page("pages/upload.py")
else:
    if not ss["redirected"]:
        logging.info("Data already processed, switching to financial analysis page...")
        # Show financial analysis page
        logging.info("Switching to financial analysis page...")
        ss["redirected"] = True
        st.switch_page("pages/financial_analysis.py")
