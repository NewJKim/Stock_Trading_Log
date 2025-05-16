# Team Project
# Team: MOLLA, Team Member: James Kim
# Stock Trading Application using Tkinter and SQLite
# Developed to track buy/sell transactions, show portfolio pie chart and price trends.
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from datetime import datetime
import pandas as pd
import requests
import sqlite3
import matplotlib.pyplot as plt

# Finnhub API key for fetching stock prices
FINNHUB_API_KEY = "d0i004pr01qji78qs6a0d0i004pr01qji78qs6ag"
current_user_id = None

# Initialize the SQLite database and tables
def init_db():
    # Connect to SQLite DB and create tables if they don't exist
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
    """)
    # Create transactions table to store buy/sell history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ticker TEXT,
            quantity REAL,
            price REAL,
            date TEXT,
            type TEXT DEFAULT 'buy',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


# Prompt user to log in by entering a username
# Creates a new user entry in the database if it doesn't exist
def login(root):
    global current_user_id
    username = simpledialog.askstring("Login", "Enter your username:", parent=root)
    # username required
    if not username:
        messagebox.showerror("Login Failed", "Username is required.")
        root.destroy()
        return False
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result:
        current_user_id = result[0]
    else:
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        current_user_id = cursor.lastrowid
    conn.close()
    return True


# Fetch current stock price from Finnhub API
def fetch_price_finnhub(ticker):
    url = "https://finnhub.io/api/v1/quote"
    params = {"symbol": ticker.upper(), "token": FINNHUB_API_KEY}
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        return data.get("c", 0.0)
    except Exception as e:
        print(f"Finnhub error for {ticker}: {e}")
        return 0.0  # return 0 for now. user can delete the data


# Add a new transaction (buy or sell) to the database
def add_transaction(txn_type):
    ticker = entry_ticker.get().upper()
    try:
        quantity = float(entry_quantity.get())
        price = float(entry_price.get())
    except ValueError:
        print("Invalid quantity or price")
        return

    date_input = entry_date.get().strip()
    if date_input:
        try:
            date = pd.to_datetime(date_input).strftime('%Y-%m-%d')
        except Exception:
            print("Invalid date format")
            return
    else:
        date = datetime.today().strftime('%Y-%m-%d')

    # Check current quantity before sell
    if txn_type == "sell":
        conn = sqlite3.connect("portfolio.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(CASE WHEN type = 'buy' THEN quantity ELSE -quantity END)
            FROM transactions
            WHERE user_id = ? AND ticker = ?
        """, (current_user_id, ticker))
        result = cursor.fetchone()
        conn.close()

        held_quantity = result[0] if result[0] else 0

        if quantity > held_quantity:
            messagebox.showerror("Error", f"You cannot sell more than you currently hold ({held_quantity} shares).")
            return

    # Save transaction
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, ticker, quantity, price, date, type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (current_user_id, ticker, quantity, price, date, txn_type))
    conn.commit()
    conn.close()

    update_table()
    clear_inputs()


# Delete selected transaction from the table and DB
def delete_transaction():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Delete Transaction", "Please select a transaction to delete.")
        return
    txn_id = int(selected[0])
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (txn_id, current_user_id))
    conn.commit()
    conn.close()
    update_table()


# Refresh the transaction table in GUI with latest data
def update_table():
    for row in tree.get_children():
        tree.delete(row)
    conn = sqlite3.connect("portfolio.db")
    df = pd.read_sql_query("SELECT * FROM transactions WHERE user_id = ?", conn, params=(current_user_id,))
    conn.close()
    if df.empty:
        return
    df["current_price"] = df["ticker"].apply(fetch_price_finnhub)
    for _, row in df.iterrows():
        tree.insert("", "end", iid=row["id"], values=(
            row["date"], row["ticker"], row["quantity"], f"{row['price']:.2f}", row["type"],
            f"{row['current_price']:.2f}"
        ))


# Clear the input fields
def clear_inputs():
    entry_ticker.delete(0, tk.END)
    entry_quantity.delete(0, tk.END)
    entry_price.delete(0, tk.END)
    entry_date.delete(0, tk.END)


# Display a pie chart of market value by ticker
def show_pie_chart():
    conn = sqlite3.connect("portfolio.db")
    df = pd.read_sql_query("SELECT * FROM transactions WHERE user_id = ?", conn, params=(current_user_id,))
    conn.close()
    if df.empty:
        messagebox.showinfo("No Data", "No transactions available.")
        return

    df["signed_quantity"] = df.apply(lambda row: row["quantity"] if row["type"] == "buy" else -row["quantity"], axis=1)
    df["cost"] = df.apply(lambda row: row["quantity"] * row["price"] if row["type"] == "buy" else 0, axis=1)

    grouped = df.groupby("ticker").agg({"signed_quantity": "sum", "cost": "sum"}).reset_index()
    grouped = grouped[grouped["signed_quantity"] > 0]

    if grouped.empty:
        messagebox.showinfo("No Holdings", "All positions have been sold.")
        return

    grouped["current_price"] = grouped["ticker"].apply(fetch_price_finnhub)
    grouped["market_value"] = grouped["signed_quantity"] * grouped["current_price"]

    total_value = grouped["market_value"].sum()

    labels = [f"{ticker} (${value:,.2f})" for ticker, value in zip(grouped["ticker"], grouped["market_value"])]
    sizes = grouped["market_value"]

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title(f"Portfolio Distribution by Market Value\nTotal: ${total_value:,.2f}")
    plt.tight_layout()
    plt.show()


# show the summary of stock holding
def show_ticker_summary():
    conn = sqlite3.connect("portfolio.db")
    df = pd.read_sql_query("SELECT * FROM transactions WHERE user_id = ?", conn, params=(current_user_id,))
    conn.close()
    if df.empty:
        messagebox.showinfo("No Data", "No transactions found.")
        return
    df["signed_quantity"] = df.apply(lambda row: row["quantity"] if row["type"] == "buy" else -row["quantity"], axis=1)
    df["cost"] = df.apply(lambda row: row["quantity"] * row["price"] if row["type"] == "buy" else 0, axis=1)
    grouped = df.groupby("ticker").agg({"signed_quantity": "sum", "cost": "sum"}).reset_index()
    grouped = grouped[grouped["signed_quantity"] > 0]
    grouped["avg_price"] = grouped["cost"] / grouped["signed_quantity"]
    grouped["current_price"] = grouped["ticker"].apply(fetch_price_finnhub)
    grouped["market_value"] = grouped["signed_quantity"] * grouped["current_price"]
    grouped["gain_loss"] = grouped["market_value"] - grouped["cost"]
    grouped["return_pct"] = (grouped["gain_loss"] / grouped["cost"]) * 100
    summary_win = tk.Toplevel(root)
    summary_win.title("Stock Summary")
    cols = ("Ticker", "Quantity", "Avg Buy", "Current", "Cost", "Value", "Gain/Loss", "Return %")
    summary_tree = ttk.Treeview(summary_win, columns=cols, show="headings")
    for col in cols:
        summary_tree.heading(col, text=col)
        summary_tree.column(col, width=100)
    summary_tree.pack(fill="both", expand=True)
    for _, row in grouped.iterrows():
        summary_tree.insert("", "end", values=(
            row["ticker"], row["signed_quantity"], f"{row['avg_price']:.2f}", f"{row['current_price']:.2f}",
            f"{row['cost']:.2f}", f"{row['market_value']:.2f}", f"{row['gain_loss']:.2f}", f"{row['return_pct']:.2f}%"
        ))

    total_cost = grouped["cost"].sum()
    total_value = grouped["market_value"].sum()
    total_gain = grouped["gain_loss"].sum()
    total_return_pct = (total_gain / total_cost) * 100 if total_cost else 0

    summary_tree.insert("", "end", values=("", "", "", "", "", "", "", ""))

    summary_tree.insert("", "end", values=(
        "TOTAL", "", "", "",
        f"{total_cost:,.2f}",
        f"{total_value:,.2f}",
        f"{total_gain:,.2f}",
        f"{total_return_pct:.2f}%"
    ))

# sort the table by user click
def sort_treeview_column(tree, col, reverse):
    items = [(tree.set(k, col), k) for k in tree.get_children('')]

    # Try to sort numerically, fallback to string
    try:
        items.sort(key=lambda t: float(t[0].replace(',', '')), reverse=reverse)
    except ValueError:
        items.sort(key=lambda t: t[0], reverse=reverse)

    for index, (val, k) in enumerate(items):
        tree.move(k, '', index)

    tree.heading(col, command=lambda: sort_treeview_column(tree, col, not reverse))


# main
def main():
    global root, tree, entry_ticker, entry_quantity, entry_price, entry_date
    init_db()
    root = tk.Tk()
    root.withdraw()
    if not login(root):
        return
    root.deiconify()
    root.title("Stock Trading Log Program")
    tk.Label(root, text="Ticker").grid(row=0, column=0)
    tk.Label(root, text="Quantity").grid(row=0, column=1)
    tk.Label(root, text="Avg Price").grid(row=0, column=2)
    tk.Label(root, text="Date (YYYYMMDD), optional").grid(row=0, column=3)
    entry_ticker = tk.Entry(root)
    entry_quantity = tk.Entry(root)
    entry_price = tk.Entry(root)
    entry_date = tk.Entry(root)
    entry_ticker.grid(row=1, column=0)
    entry_quantity.grid(row=1, column=1)
    entry_price.grid(row=1, column=2)
    entry_date.grid(row=1, column=3)
    tk.Button(root, text="Buy", command=lambda: add_transaction("buy")).grid(row=1, column=4)
    tk.Button(root, text="Sell", command=lambda: add_transaction("sell")).grid(row=1, column=5)

    tk.Label(root, text="Transaction History", font=("Arial", 16, "bold")).grid(row=2, column=0, columnspan=6,
                                                                                pady=(10, 0))

    columns = ("Date", "Ticker", "Quantity", "Avg Price", "Type", "Current Price")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: sort_treeview_column(tree, c, False))
        tree.column(col, width=150)
    tree.grid(row=3, column=0, columnspan=6)

    tk.Button(root, text="Delete", command=delete_transaction).grid(row=3, column=6)
    tk.Label(root, text="Select a row and click Delete\nto remove a transaction\nIf Current Price is 0, delete it").grid(row=3, column=7)
    tk.Button(root, text="Show Pie Chart", command=show_pie_chart).grid(row=5, column=0, pady=10)
    tk.Button(root, text="Show Stock Summary", command=show_ticker_summary).grid(row=5, column=1, pady=10)
    update_table()
    root.mainloop()


if __name__ == '__main__':
    main()
