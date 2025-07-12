import streamlit as st
from streamlit import session_state as ss
from src.readers.cashbook import CashbookReader
from src.readers.wingold import WingoldReader
from src.readers.qtr import QTRReader
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

    qtr = st.file_uploader(
        "Upload your QTR file",
        type=["xls", "xlsx"],
        key="qtr_uploader",
        help="Upload your QTR file here. It should be an Excel file with the necessary sheets.",
    )

    return cashbook_uploader, wingold_uploader, qtr


def main():
    cashbook, wingold, qtr = show_uploaders()
    button = st.button("Process Data")
    if not cashbook or not wingold:
        st.warning("Please upload your cashbook and Wingold files.")
        st.stop()
    elif not button:
        st.stop()
    elif button:
        with st.spinner("Saving files..."):
            with open("data/uploaded/cashbook.xlsx", "wb") as f:
                f.write(cashbook.getbuffer())
            with open("data/uploaded/wingold.mdb", "wb") as f:
                f.write(wingold.getbuffer())

        with st.spinner("Processing data..."):
            # Set cashbook data
            ss["cashbook"] = CashbookReader(
                "data/uploaded/cashbook.xlsx",
                "data/static/expense_categories.json",
                "data/static/income_categories.json",
                "data/static/fixed_costs.json",
                only_this_year=True,
            )

            # Extract all sales data
            wingold = WingoldReader("data/uploaded/wingold.mdb")
            qtr = QTRReader("data/uploaded/qtr.xls")

            sales = Sales()
            # Add sales data from WinGold
            wingold_mapping = {
                "DocNumber": "Invoice Number",
                "DocDate": "Date",
                "TAName": "Customer",
                "ItemCode": "Item Code",
                "Purity": "Purity",
                "QtyInPcs": "Unit Quantity",
                "GrossWt": "Gross Weight",
                "PureWt": "Pure Weight",
                "MakingRt": "Making Rate",
                "MakingValue": "Making Value",
            }
            sales.add_data(wingold.sales, mapping=wingold_mapping)

            # Add sales data from QTR
            qtr_mapping = {
                "Voucher": "Invoice Number",
                "Date": "Date",
                "Account": "Customer",
                "Weight": "Gross Weight",
                "Pure": "Pure Weight",
                "M-Charge": "Making Value",
            }
            sales.add_data(qtr.data, mapping=qtr_mapping)

            # Set sales
            ss["sales"] = sales
            st.switch_page("pages/sales_overview.py")


if __name__ == "__main__":
    main()
