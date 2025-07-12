from streamlit import session_state as ss
import streamlit as st
import sys

sys.dont_write_bytecode = True  # Prevents creation of .pyc files

from utils import present_navigation
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s\t%(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # Restricts to seconds
    force=True,
)

st.set_page_config(layout="wide")

# Flag to check if the user has already processed data
if "redirected" not in ss:
    ss["redirected"] = False

present_navigation()
if "cashbook" not in ss or "sales" not in ss:
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
