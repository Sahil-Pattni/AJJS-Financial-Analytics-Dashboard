import streamlit as st


def present_navigation():
    pages = {
        "Control Panel": [st.Page("pages/upload.py", title="Upload Files")],
        "Analysis": [
            st.Page("pages/financial_analysis.py", title="Financial Analysis"),
            st.Page("pages/client_sales.py", title="Client Sales"),
            st.Page("pages/sales_overview.py", title="Sales Overview"),
        ],
        "Simulations": [
            st.Page("pages/revenue_simulation.py", title="Revenue Simulation"),
        ],
    }

    st.navigation(pages).run()
