import streamlit as st


def present_navigation():
    pages = {
        "Analysis": [
            st.Page("pages/financial_analysis.py", title="Financial Analysis"),
        ],
        "Control Panel": [st.Page("pages/upload.py", title="Upload Files")],
    }

    st.navigation(pages).run()
