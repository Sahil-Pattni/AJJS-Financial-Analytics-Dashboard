# AJJS Financial Analytics Dashboard
A financial analytics dashboard and data aggregation tool for Al Joury Jewellers Smith, built with Streamlit and Plotly.

### Features

- **Data Aggregation**: Collects and aggregates sales data from multiple sources.
   - **Visual WinGold**: Collects and parses data from Visual WinGold's underlying Microsoft Access database using the `mdb-tools` external library.
   - **Cashbook(s)**: Collects and parses data from multiple cashbook sheets within encrypted Excel files using the `msoffcrypto` library.
 - **Data Analysis**: Provides various data analysis features, including:
   - **Bar Chart**: Month-wise Cost/Revenue, with the ability to factor in gold purity gains at a specified market rate.
   - **Sunburst Pie Chart**: Fixed-cost analysis, showing the breakdown of fixed costs by category and sub-category.
   - **Bar Chart**: Month-wise revenue trends by item purity.
   - **Sunburst Pie Chart**: Revenue breakdown by item purity and item category.
   - **Whisker Box Plot**: Weekly revenue by month.
   - **Histogram**: Weekly sales quantity (gross weight), with a Savitzky-Golay smoothed rolling average line.
   - **Histogram**: Weight distribution by item category and purity.
   - **Box Plot**: Item weight distribution by item category and purity.
- **Advanced Filtering**:
  - **Client Filtering**: Allows users to filter data by client, enabling focused analysis on specific customer segments.
  - **Date Range Filtering**: Enables users to filter data by a specific date range, providing flexibility in analyzing trends over time. 
  - **Item Category and Purity Filtering**: Allows users to filter weight distribution data by item category and purity, enabling more granular analysis.