import cv2
from pyzbar.pyzbar import decode
import qrcode
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from mysql.connector import Error as DBError

from db_connection import get_connection

# =====================================================
# SCAN QR AND ADD PRODUCT
# =====================================================

def scan_add_product():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        messagebox.showerror("Error", "Camera Not Available")
        return

    con = get_connection()
    cursor = con.cursor()

    messagebox.showinfo("Scanner", "Show QR Code To Camera\nPress Q To Close")
    scanned = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        for barcode in decode(frame):
            qr_data = barcode.data.decode("utf-8")

            try:
                # Expected format: pid|name|company|price|category
                data = qr_data.split("|")
                pid = int(data[0])
                name = data[1]
                price = int(data[3])
                category = data[4] if len(data) > 4 else "General"

                qty = simpledialog.askinteger("Quantity", f"Enter Quantity For {name}:")
                if qty is None:
                    scanned = True
                    break

                cursor.execute("SELECT stock FROM products WHERE id=%s", (pid,))
                result = cursor.fetchone()

                if result:
                    new_stock = result[0] + qty
                    cursor.execute("UPDATE products SET stock=%s WHERE id=%s", (new_stock, pid))
                    messagebox.showinfo("Updated", f"Stock Updated\nNew Stock = {new_stock}")
                else:
                    cursor.execute(
                        "INSERT INTO products(id,name,category,price,stock) VALUES(%s,%s,%s,%s,%s)",
                        (pid, name, category, price, qty)
                    )
                    messagebox.showinfo("Success", f"New Product Added in '{category}' Category")

                con.commit()
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

        cv2.imshow("Inventory Scanner", frame)

        if scanned or cv2.waitKey(1) == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    con.close()

# =====================================================
# MANUAL ADD PRODUCT
# =====================================================

def manual_add():
    pid = simpledialog.askinteger("Input", "Enter Product ID:")
    if pid is None:
        return

    name = simpledialog.askstring("Input", "Enter Product Name (e.g., Milk, Apple, Flour):")
    if not name:
        return

    company = simpledialog.askstring("Input", "Enter Brand/Company Name:")
    if not company:
        company = "Generic"

    category = simpledialog.askstring(
        "Category", 
        "Enter Category (e.g., Dairy, Grocery, Fruits, Vegetables, Bakery):"
    )
    if not category:
        category = "General"

    price = simpledialog.askinteger("Input", "Enter Price:")
    if price is None:
        return

    qty = simpledialog.askinteger("Input", "Enter Quantity:")
    if qty is None:
        return

    con = get_connection()
    cursor = con.cursor()

    try:
        cursor.execute(
            "INSERT INTO products(id,name,category,price,stock) VALUES(%s,%s,%s,%s,%s)",
            (pid, name, category, price, qty)
        )
        con.commit()

        qr_data = f"{pid}|{name}|{company}|{price}|{category}"
        img = qrcode.make(qr_data)
        img.save(f"{pid}.png")

        messagebox.showinfo("Success", f"Product Added under '{category}'\nQR Saved As {pid}.png")

    except DBError as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        con.close()

# =====================================================
# REMOVE & CHECK PRODUCT
# =====================================================

def remove_product():
    pid = simpledialog.askinteger("Remove Product", "Enter Product ID:")
    if pid is None:
        return

    con = get_connection()
    cursor = con.cursor()
    cursor.execute("DELETE FROM products WHERE id=%s", (pid,))
    con.commit()

    if cursor.rowcount > 0:
        messagebox.showinfo("Success", "Product Removed")
    else:
        messagebox.showwarning("Not Found", "Product Not Found")
    con.close()

def check_status():
    pid = simpledialog.askinteger("Check Product", "Enter Product ID:")
    if pid is None:
        return

    con = get_connection()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM products WHERE id=%s", (pid,))
    row = cursor.fetchone()

    if row:
        stock = row[4]
        status = "Out Of Stock" if stock == 0 else ("Low Stock" if stock < 5 else "Available")
        messagebox.showinfo(
            "Product Details",
            f"ID : {row[0]}\nName : {row[1]}\nCategory : {row[2]}\nPrice : \u20b9{row[3]}\nStock : {row[4]}\nStatus : {status}"
        )
    else:
        messagebox.showwarning("Not Found", "Product Not Found")
    con.close()

# =====================================================
# SHOW PRODUCTS TABLE
# =====================================================

def show_products():
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("SELECT id, name, category, price, stock FROM products ORDER BY category, name")
    data = cursor.fetchall()
    con.close()

    if not data:
        messagebox.showinfo("Inventory", "No Products Found")
        return

    win = tk.Toplevel(root)
    win.title("Inventory Products")
    win.geometry("850x450")
    win.config(bg="#1e1e2f")

    tk.Label(
        win, text="PRODUCT INVENTORY (CATEGORY WISE)", font=("Arial", 18, "bold"),
        bg="#1e1e2f", fg="white"
    ).pack(pady=10)

    frame = tk.Frame(win)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(frame)
    tree.pack(fill="both", expand=True)

    tree["columns"] = ("ID", "Name", "Category", "Price", "Stock")
    tree["show"] = "headings"

    for col in ("ID", "Name", "Category", "Price", "Stock"):
        tree.heading(col, text=col)
        tree.column(col, width=150)

    for row in data:
        tree.insert("", "end", values=row)

# =====================================================
# MAIN GUI
# =====================================================

root = tk.Tk()
root.title("Modern Inventory System")
root.geometry("500x700")
root.config(bg="#1e1e2f")

tk.Label(root, text="INVENTORY SYSTEM", font=("Arial", 24, "bold"), bg="#1e1e2f", fg="white").pack(pady=20)
tk.Label(root, text="Inventory Project Dashboard", font=("Arial", 11), bg="#1e1e2f", fg="#cccccc").pack()

style = {
    "font": ("Arial", 13, "bold"),
    "width": 28,
    "height": 2,
    "fg": "white",
    "bd": 0,
    "cursor": "hand2"
}

tk.Button(root, text="1. Scan QR And Add Product", command=scan_add_product, bg="#3498db", **style).pack(pady=10)
tk.Button(root, text="2. Manual Add + Generate QR", command=manual_add, bg="#27ae60", **style).pack(pady=10)
tk.Button(root, text="3. Remove Product", command=remove_product, bg="#f39c12", **style).pack(pady=10)
tk.Button(root, text="4. Check Product Status", command=check_status, bg="#9b59b6", **style).pack(pady=10)
tk.Button(root, text="5. Show All Products", command=show_products, bg="#16a085", **style).pack(pady=10)
tk.Button(root, text="6. Exit", command=root.destroy, bg="#e74c3c", **style).pack(pady=10)

root.mainloop()