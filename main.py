import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

inventory_file = "inventory.py"
billing_file = "billing.py"
sales_file = "sales.py"

def run_program(filename):
    if os.path.exists(filename):
        subprocess.Popen([sys.executable, filename])
    else:
        messagebox.showerror("File Not Found", f"{filename} not found")

def open_inventory():
    run_program(inventory_file)

def open_billing():
    run_program(billing_file)

def open_sales():
    run_program(sales_file)

root = tk.Tk()
root.title("Shop Management System")
root.geometry("500x650")
root.config(bg="#1e1e2f")

tk.Label(
    root, text="SHOP MANAGEMENT", font=("Arial", 24, "bold"),
    bg="#1e1e2f", fg="white"
).pack(pady=20)

tk.Label(
    root, text="Main Dashboard", font=("Arial", 11),
    bg="#1e1e2f", fg="#cccccc"
).pack()

style = {
    "font": ("Arial", 14, "bold"),
    "width": 28,
    "height": 2,
    "fg": "white",
    "bd": 0,
    "cursor": "hand2"
}

tk.Button(root, text="1. Inventory System", command=open_inventory, bg="#3498db", **style).pack(pady=15)
tk.Button(root, text="2. Billing System", command=open_billing, bg="#27ae60", **style).pack(pady=15)
tk.Button(root, text="3. Sales Analysis", command=open_sales, bg="#9b59b6", **style).pack(pady=15)
tk.Button(root, text="4. Exit", command=root.destroy, bg="#e74c3c", **style).pack(pady=25)

tk.Label(
    root, text="Purva Kavathekar", font=("Arial", 10),
    bg="#1e1e2f", fg="#aaaaaa"
).pack(side="bottom", pady=20)

root.mainloop()