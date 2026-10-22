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

    pid = simpledialog.askinteger(
        "Remove Product",
        "Enter Product ID:"
    )

    if pid is None:
        return

    # Find the product in the bill
    item = None

    for product in bill:
        if product[0] == pid:
            item = product
            break

    if item is None:
        messagebox.showwarning(
            "Not Found",
            "Product Not Found in Bill"
        )
        return

    choice = messagebox.askyesnocancel(
        "Modify Product",
        f"Product: {item[1]}\n"
        f"Current Quantity: {item[4]}\n\n"
        "Yes = Remove Completely\n"
        "No = Change Quantity\n"
        "Cancel = Go Back"
    )

    if choice is None:
        return

    con = get_connection()
    cursor = con.cursor()

    try:
        if choice is True:
            # Remove the entire product
            bill.remove(item)
            grand_total -= item[5]

            cursor.execute(
                "UPDATE products SET stock = stock + %s WHERE id = %s",
                (item[4], pid)
            )

            message = "Product Removed Successfully"

        else:
            # Ask for the FINAL quantity to keep
            new_qty = simpledialog.askinteger(
                "Change Quantity",
                f"Product: {item[1]}\n"
                f"Current Quantity: {item[4]}\n"
                "Enter the quantity you want to keep:",
                minvalue=0,
                maxvalue=item[4]
            )

            if new_qty is None:
                return

            old_qty = item[4]
            old_amount = item[5]

            # Calculate price per unit
            unit_price = old_amount / old_qty

            # Calculate quantity being returned to stock
            returned_qty = old_qty - new_qty

            cursor.execute(
                "UPDATE products SET stock = stock + %s WHERE id = %s",
                (returned_qty, pid)
            )

            if new_qty == 0:
                # Zero quantity means remove completely
                bill.remove(item)
                grand_total -= old_amount

                message = "Product Removed Successfully"

            else:
                # Update the bill with the new quantity
                new_amount = round(new_qty * unit_price, 2)

                item[4] = new_qty
                item[5] = new_amount

                grand_total -= (old_amount - new_amount)

                message = (
                    f"Quantity updated successfully!\n"
                    f"New Quantity: {new_qty}\n"
                    f"New Amount: ₹{new_amount:.2f}"
                )

        con.commit()

        messagebox.showinfo("Success", message)

    except Exception as e:
        con.rollback()
        messagebox.showerror(
            "Database Error",
            f"Could not update product: {e}"
        )

    finally:
        cursor.close()
        con.close()

    # Refresh the bill display here if required.


# =====================================================
# FINISH BILL
# =====================================================


from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import tkinter as tk


def finish_bill():
    global bill, grand_total

    if not bill:
        messagebox.showinfo("Bill", "Bill is Empty")
        return

    con = get_connection()
    cursor = con.cursor()

    try:
        # Generate the next bill number automatically
        cursor.execute("SELECT COALESCE(MAX(billno), 1000) + 1 FROM sales")
        billno = cursor.fetchone()[0]

        # Save all products under the same bill number
        for item in bill:
            cursor.execute(
                """
                INSERT INTO sales
                (billno, pid, name, category, qty, amount)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (billno, item[0], item[1], item[2],
                 item[4], item[5])
            )

        con.commit()

        # Prepare receipt
        receipt_time = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

        receipt = []
        receipt.append("=" * 48)
        receipt.append("              SHOP BILL RECEIPT")
        receipt.append("=" * 48)
        receipt.append(f"Bill Number : {billno}")
        receipt.append(f"Date        : {receipt_time}")
        receipt.append("-" * 48)
        receipt.append(
            f"{'Product':<22}{'Qty':>5}{'Price':>9}{'Total':>10}"
        )
        receipt.append("-" * 48)

        for item in bill:
            pid, name, category, price, qty, amount = item

            # Wrap long product names if needed
            receipt.append(
                f"{name[:21]:<22}{qty:>5}"
                f"{price:>9.2f}{amount:>10.2f}"
            )

        receipt.append("-" * 48)
        receipt.append(f"Grand Total: Rs. {grand_total:.2f}")
        receipt.append("=" * 48)
        receipt.append("       Thank you for shopping!")
        receipt.append("=" * 48)

        receipt_text = "\n".join(receipt)

        # Display receipt in a separate window
        receipt_window = tk.Toplevel()
        receipt_window.title(f"Receipt - Bill {billno}")
        receipt_window.geometry("620x520")

        text_area = ScrolledText(
            receipt_window,
            font=("Courier New", 11),
            wrap=tk.NONE
        )
        text_area.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=10
        )

        text_area.insert(tk.END, receipt_text)
        text_area.config(state=tk.DISABLED)

        # Optional: print receipt text in the console
        print(receipt_text)

        # Clear the current bill only after saving
        final_total = grand_total 
        bill = []
        grand_total = 0

        messagebox.showinfo(
        "Success",
        f"Bill Saved Successfully!\n"
        f"Bill Number: {billno}\n"
        f"Grand Total: Rs. {final_total:.2f}"
       )

    except Exception as e:
        con.rollback()
        messagebox.showerror("Database Error", str(e))

    finally:
        cursor.close()
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