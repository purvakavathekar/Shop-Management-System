import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod

from db_connection import get_connection

class Report(ABC):
    @abstractmethod
    def generate(self):
        pass

class SalesReport(Report):
    def generate(self):
        return get_sales_data()

def get_sales_data():
    con = get_connection()
    query = "SELECT * FROM sales"
    df = pd.read_sql(query, con)
    con.close()
    return df

def show_report():
    report = SalesReport()
    df = report.generate()

    if df.empty:
        messagebox.showinfo("Sales", "No Sales Data Available")
        return

    df["price"] = df["amount"] / df["qty"]

    win = tk.Toplevel(root)
    win.title("Full Sales Report")
    win.geometry("900x500")
    win.config(bg="#1e1e2f")

    tk.Label(win, text="FULL SALES REPORT", font=("Arial", 18, "bold"), bg="#1e1e2f", fg="white").pack(pady=10)

    tree = ttk.Treeview(win)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    tree["columns"] = ("billno", "pid", "name", "category", "price", "qty", "amount")
    tree["show"] = "headings"

    for col in ("billno", "pid", "name", "category", "price", "qty", "amount"):
        tree.heading(col, text=col.capitalize())
        tree.column(col, width=120)

    for _, row in df.iterrows():
        tree.insert(
            "", "end",
            values=(row["billno"], row["pid"], row["name"], row["category"], f"\u20b9{row['price']:.2f}", row["qty"], f"\u20b9{row['amount']}")
        )

# =====================================================
# CATEGORY-WISE SALES BREAKDOWN
# =====================================================

def category_sales():
    df = get_sales_data()
    if df.empty:
        messagebox.showinfo("Sales", "No Data Available")
        return

    result = df.groupby("category")["amount"].agg(["sum", "count"]).reset_index()
    result.columns = ["Category", "Total Revenue", "Transactions"]

    text = "CATEGORY-WISE SALES SUMMARY\n" + "="*35 + "\n\n"
    for _, row in result.iterrows():
        text += f"• {row['Category']}:\n   Revenue: \u20b9{row['Total Revenue']} | Transactions: {row['Transactions']}\n\n"

    top_cat = result.loc[result['Total Revenue'].idxmax()]['Category']
    text += f"Top Performing Category: {top_cat}"

    messagebox.showinfo("Category Sales Analysis", text)

def total_sales():
    df = get_sales_data()
    if df.empty:
        messagebox.showinfo("Sales", "No Data Available")
        return

    total = df["amount"].sum()
    messagebox.showinfo("Total Sales", f"Total Sales Amount = \u20b9{total}")

def product_sales():
    df = get_sales_data()
    if df.empty:
        messagebox.showinfo("Sales", "No Data Available")
        return

    result = df.groupby(["category", "name"])["amount"].sum()

    text = "PRODUCT SALES BY CATEGORY\n\n"
    for (cat, name), amount in result.items():
        text += f"[{cat}] {name} = \u20b9{amount}\n"

    messagebox.showinfo("Product Sales", text)

def export_csv():
    df = get_sales_data()
    if df.empty:
        messagebox.showinfo("CSV", "No Data Available")
        return

    df.to_csv("sales_report.csv", index=False)
    messagebox.showinfo("Success", "sales_report.csv Saved Successfully")

# =====================================================
# CATEGORY GRAPH VISUALIZATION
# =====================================================

def show_graph():
    df = get_sales_data()
    if df.empty:
        messagebox.showinfo("Graph", "No Data Available")
        return

    cat_result = df.groupby("category")["amount"].sum()

    win = tk.Toplevel(root)
    win.title("Category Sales Graph")
    win.geometry("800x500")

    fig, ax = plt.subplots(figsize=(10, 6))
    cat_result.plot(kind="bar", ax=ax, color="#3498db")

    ax.set_title("Revenue by Product Category", fontsize=14, fontweight="bold")
    ax.set_xlabel("Category", fontsize=12)
    ax.set_ylabel("Revenue (\u20b9)", fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# =====================================================
# MAIN GUI
# =====================================================

root = tk.Tk()
root.title("Modern Sales Analysis")
root.geometry("500x700")
root.config(bg="#1e1e2f")

tk.Label(root, text="SALES ANALYSIS", font=("Arial", 24, "bold"), bg="#1e1e2f", fg="white").pack(pady=20)
tk.Label(root, text="Category-Aware Analytics", font=("Arial", 11), bg="#1e1e2f", fg="#cccccc").pack()

style = {"font": ("Arial", 13, "bold"), "width": 28, "height": 2, "fg": "white", "bd": 0}

tk.Button(root, text="1. Full Sales Report", command=show_report, bg="#E5AA7B", **style).pack(pady=8)
tk.Button(root, text="2. Category Wise Sales", command=category_sales, bg="#27ae60", **style).pack(pady=8)
tk.Button(root, text="3. Product Wise Sales", command=product_sales, bg="#3F1816", **style).pack(pady=8)
tk.Button(root, text="4. Total Sales Revenue", command=total_sales, bg="#A9835C", **style).pack(pady=8)
tk.Button(root, text="5. Show Category Graph", command=show_graph, bg="#222918", **style).pack(pady=8)
tk.Button(root, text="6. Export CSV", command=export_csv, bg="#90A3AF", **style).pack(pady=8)
tk.Button(root, text="7. Exit", command=root.destroy, bg="#003F55", **style).pack(pady=15)

root.mainloop()