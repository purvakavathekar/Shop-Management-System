import cv2
from pyzbar.pyzbar import decode
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from mysql.connector import Error as DBError

from db_connection import get_connection

# =====================================================
# GLOBAL BILL & TRACKING
# =====================================================

bill = []
grand_total = 0

# =====================================================
# SHOW BILL TABLE
# =====================================================

def show_bill():
    global bill, grand_total
    if not bill:
        messagebox.showinfo("Bill", "Bill is Empty")
        return

    win = tk.Toplevel(root)
    win.title("Current Bill")
    win.geometry("800x450")
    win.config(bg="#1e1e2f")

    tk.Label(win, text="CURRENT BILL", font=("Arial", 18, "bold"), bg="#1e1e2f", fg="white").pack(pady=10)
    frame = tk.Frame(win)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(frame)
    tree.pack(fill="both", expand=True)

    tree["columns"] = ("ID", "Name", "Category", "Price", "Qty", "Amount")
    tree["show"] = "headings"

    for col in ("ID", "Name", "Category", "Price", "Qty", "Amount"):
        tree.heading(col, text=col)
        tree.column(col, width=120)

    for item in bill:
        tree.insert("", "end", values=item)

    tk.Label(win, text=f"Grand Total = \u20b9{grand_total}", font=("Arial", 14, "bold"), bg="#1e1e2f", fg="#00ff99").pack(pady=10)

# =====================================================
# SCAN PRODUCT VIA QR CODE
# =====================================================

def scan_product():
    global bill, grand_total
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        messagebox.showerror("Error", "Camera Not Available")
        return

    con = get_connection()
    cursor = con.cursor()
    messagebox.showinfo("Scanner", "Show QR Code to Camera\nPress Q to Close")
    scanned = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        for barcode in decode(frame):
            qr_data = barcode.data.decode("utf-8")
            try:
                data = qr_data.split("|")
                pid = int(data[0])
                name = data[1]
                price = int(data[3])

                qty = simpledialog.askinteger("Quantity", f"Enter Quantity for {name}:")
                if qty is None:
                    scanned = True
                    break

                cursor.execute("SELECT stock, category FROM products WHERE id=%s", (pid,))
                result = cursor.fetchone()

                if result:
                    stock, category = result[0], result[1]

                    if qty <= stock:
                        amount = qty * price
                        grand_total += amount
                        bill.append([pid, name, category, price, qty, amount])

                        new_stock = stock - qty
                        cursor.execute("UPDATE products SET stock=%s WHERE id=%s", (new_stock, pid))
                        con.commit()
                        messagebox.showinfo("Success", f"{name} ({category}) Added to Bill")
                    else:
                        messagebox.showwarning("Stock", "Not Enough Stock Available")
                else:
                    messagebox.showwarning("Not Found", "Product Not Found")

                scanned = True
                break

            except (ValueError, IndexError):
                messagebox.showerror("Error", "Invalid QR Code Format")
                scanned = True
                break
            except DBError as e:
                messagebox.showerror("Database Error", str(e))
                scanned = True
                break

        cv2.imshow("Billing Scanner", frame)
        if scanned or cv2.waitKey(1) == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    con.close()

# =====================================================
# MANUAL ADD TO BILL (NEW FEATURE)
# =====================================================

def manual_add_to_bill():
    global bill, grand_total

    pid = simpledialog.askinteger("Manual Billing", "Enter Product ID:")
    if pid is None:
        return

    con = get_connection()
    cursor = con.cursor()

    try:
        cursor.execute("SELECT name, category, price, stock FROM products WHERE id=%s", (pid,))
        result = cursor.fetchone()

        if not result:
            messagebox.showwarning("Not Found", f"No product found with ID {pid}")
            return

        name, category, price, stock = result[0], result[1], result[2], result[3]

        if stock <= 0:
            messagebox.showwarning("Out of Stock", f"{name} is currently Out of Stock!")
            return

        qty = simpledialog.askinteger(
            "Quantity", 
            f"Product: {name}\nCategory: {category}\nPrice: \u20b9{price}\nAvailable Stock: {stock}\n\nEnter Quantity:"
        )
        if qty is None or qty <= 0:
            return

        if qty <= stock:
            amount = qty * price
            grand_total += amount
            bill.append([pid, name, category, price, qty, amount])

            new_stock = stock - qty
            cursor.execute("UPDATE products SET stock=%s WHERE id=%s", (new_stock, pid))
            con.commit()
            messagebox.showinfo("Success", f"{qty} x {name} Added to Bill (\u20b9{amount})")
        else:
            messagebox.showwarning("Insufficient Stock", f"Only {stock} items available in stock!")

    except DBError as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        con.close()

# =====================================================
# REMOVE PRODUCT FROM BILL
# =====================================================

def remove_product():
    global bill, grand_total
    if not bill:
        messagebox.showinfo("Bill", "Bill is Empty")
        return

    pid = simpledialog.askinteger("Remove Product", "Enter Product ID:")
    if pid is None:
        return

    con = get_connection()
    cursor = con.cursor()
    found = False

    for item in bill:
        if item[0] == pid:
            bill.remove(item)
            grand_total -= item[5]
            cursor.execute("UPDATE products SET stock = stock + %s WHERE id=%s", (item[4], pid))
            con.commit()
            found = True
            break

    con.close()
    if found:
        messagebox.showinfo("Removed", "Product Removed Successfully")
    else:
        messagebox.showwarning("Not Found", "Product Not Found in Bill")

# =====================================================
# FINISH BILL
# =====================================================

def finish_bill():
    global bill, grand_total
    if not bill:
        messagebox.showinfo("Bill", "Bill is Empty")
        return

    billno = simpledialog.askinteger("Bill Number", "Enter Bill Number:")
    if billno is None:
        return

    con = get_connection()
    cursor = con.cursor()

    try:
        for item in bill:
            cursor.execute(
                """
                INSERT INTO sales(billno, pid, name, category, qty, amount)
                VALUES(%s,%s,%s,%s,%s,%s)
                """,
                (billno, item[0], item[1], item[2], item[4], item[5])
            )

        con.commit()
        messagebox.showinfo("Success", f"Bill Saved Successfully\nGrand Total = \u20b9{grand_total}")
        bill = []
        grand_total = 0

    except DBError as e:
        con.rollback()
        messagebox.showerror("Database Error", str(e))
    finally:
        con.close()

# =====================================================
# CLEAR BILL
# =====================================================

def clear_bill():
    global bill, grand_total
    bill = []
    grand_total = 0
    messagebox.showinfo("Cleared", "Bill Cleared")

# =====================================================
# MAIN GUI DASHBOARD
# =====================================================

root = tk.Tk()
root.title("Modern Billing System")
root.geometry("500x720")
root.config(bg="#1e1e2f")

tk.Label(root, text="BILLING SYSTEM", font=("Arial", 24, "bold"), bg="#1e1e2f", fg="white").pack(pady=15)
tk.Label(root, text="Inventory & Retail Billing Dashboard", font=("Arial", 11), bg="#1e1e2f", fg="#cccccc").pack()

style = {"font": ("Arial", 12, "bold"), "width": 28, "height": 2, "fg": "white", "bd": 0, "cursor": "hand2"}

tk.Button(root, text="1. Scan Product (QR Code)", command=scan_product, bg="#3498db", **style).pack(pady=8)
tk.Button(root, text="2. Manual Add Product to Bill", command=manual_add_to_bill, bg="#e67e22", **style).pack(pady=8)
tk.Button(root, text="3. Show Current Bill", command=show_bill, bg="#27ae60", **style).pack(pady=8)
tk.Button(root, text="4. Remove Product", command=remove_product, bg="#f39c12", **style).pack(pady=8)
tk.Button(root, text="5. Finish Bill", command=finish_bill, bg="#9b59b6", **style).pack(pady=8)
tk.Button(root, text="6. Clear Bill", command=clear_bill, bg="#16a085", **style).pack(pady=8)
tk.Button(root, text="7. Exit", command=root.destroy, bg="#e74c3c", **style).pack(pady=12)

root.mainloop()