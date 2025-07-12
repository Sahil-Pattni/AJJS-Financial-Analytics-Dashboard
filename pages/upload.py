import streamlit as st
from streamlit import session_state as ss
from src.readers.cashbook import CashbookReader
from src.readers.wingold import WingoldReader
from src.models.sales import Sales


def show_uploaders():
    cashbook_uploader = st.file_uploader(
        "Upload your cashbook file",
        type=["xls", "xlsx", "xlsm"],
        key="cashbook_uploader",
        help="Upload your cashbook file here. It should be an Excel file with the necessary sheets.",
    )

    wingold_uploader = st.file_uploader(
        "Upload your Wingold file",
        type=["mdb"],
        key="wingold_uploader",
        help="Upload your Wingold file here. It should be a Microsoft Access Database file.",
    )

    return cashbook_uploader, wingold_uploader


def main():
    cashbook, wingold = show_uploaders()
    if not cashbook or not wingold:
        st.warning("Please upload your cashbook and Wingold files.")
        st.stop()

    with st.spinner("Saving files..."):
        with open("data/uploaded/cashbook.xlsx", "wb") as f:
            f.write(cashbook.getbuffer())
        with open("data/uploaded/wingold.mdb", "wb") as f:
            f.write(wingold.getbuffer())

    with st.spinner("Processing data..."):
        ss["cashbook"] = CashbookReader(
            "data/uploaded/cashbook.xlsx",
            "data/static/expense_categories.json",
            "data/static/income_categories.json",
            "data/static/fixed_costs.json",
            only_this_year=True,
        )

        wingold = WingoldReader("data/uploaded/wingold.mdb")
        sales = Sales()
        sales.add_data(wingold.sales)
        ss["sales"] = sales
        st.switch_page("pages/sales_overview.py")


if __name__ == "__main__":
    main()
