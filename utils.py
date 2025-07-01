import streamlit as st


def present_navigation():
    pages = {
        "Control Panel": [st.Page("pages/upload.py", title="Upload Files")],
        "Analysis": [
            st.Page("pages/financial_analysis.py", title="Financial Analysis"),
        ],
    }

    st.navigation(pages).run()
