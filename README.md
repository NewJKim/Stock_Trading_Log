# Stock_Trading_Log
CS2520 Team Project

# Stock Trading Tracker (Python + Tkinter)

A Python GUI application to track stock buy/sell transactions, calculate portfolio performance, and visualize asset distribution using real-time data.

---

## Features

-  **User Login**: Tracks transactions per user (stored in local SQLite database)
-  **Buy/Sell Transactions**: Record stock trades with ticker, quantity, price, and date
-  **Stock Summary View**: View average cost, current price, total value, gain/loss, and return%
-  **Pie Chart Visualization**: Visualize asset allocation by market value
-  **Sell Restrictions**: Prevents users from selling more than they own
-  **Sortable Table**: View and sort transaction history by clicking table headers
-  **Data Persistence**: All data saved locally using `sqlite3`

---

## 🛠 Built With

- [Python 3.10+](https://www.python.org/)
- [`tkinter`](https://docs.python.org/3/library/tkinter.html) - GUI framework
- [`sqlite3`](https://docs.python.org/3/library/sqlite3.html) - Embedded database
- [`pandas`](https://pandas.pydata.org/) - Data processing
- [`matplotlib`](https://matplotlib.org/) - Charts and graphs
- [`requests`](https://docs.python-requests.org/) - API integration for stock prices (via [Finnhub API](https://finnhub.io))
