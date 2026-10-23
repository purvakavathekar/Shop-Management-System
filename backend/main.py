import base64
import io
import os
from contextlib import contextmanager
from datetime import datetime

import mysql.connector
import qrcode
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

# Enable CORS once for all origins (supports local dev and live Render frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://shop-management-system-1-fbkx.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Read dynamic MySQL settings from Render Environment Variables (or fallback to local .env)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 11342))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "defaultdb")

QR_FOLDER = "qr_codes"

# =====================================================
# HELPERS
# =====================================================

def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        ssl_ca="ca.pem",  # <--- Point to your downloaded certificate
        ssl_verify_cert=True, # <--- Enforce verification
        connection_timeout=10,
    )


@contextmanager
def db():
    conn = get_db()
    try:
        yield conn
    finally:
        if conn.is_connected():
            conn.close()


def db_error(e):
    # 1062 = duplicate primary key
    if getattr(e, "errno", None) == 1062:
        return HTTPException(status_code=400, detail="A product with this ID already exists")
    return HTTPException(status_code=500, detail=str(e))


def num(x):
    """Return clean numbers for JSON (120 instead of Decimal('120.00'))."""
    x = float(x)
    return int(x) if x.is_integer() else round(x, 2)


def make_qr(pid, name, company, price, category):
    """Same QR format as inventory.py: pid|name|company|price|category"""
    data = f"{pid}|{name}|{company}|{price}|{category}"
    img = qrcode.make(data)

    os.makedirs(QR_FOLDER, exist_ok=True)
    img.save(os.path.join(QR_FOLDER, f"{pid}.png"))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# =====================================================
# MODELS
# =====================================================

class UserAuthRequest(BaseModel):
    username: str
    password: str


class ProductCreate(BaseModel):
    id: int
    name: str
    company: str = "Generic"
    category: str = "General"
    price: int
    stock: int


class ScanProduct(BaseModel):
    id: int
    name: str
    category: str = "General"
    price: int
    stock: int


class CartAdd(BaseModel):
    id: int
    qty: int


class CartModify(BaseModel):
    id: int
    new_qty: int


# =====================================================
# BASIC
# =====================================================

@app.get("/")
def home():
    return {"message": "Shop Management System API is running!", "status": "success"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# =====================================================
# AUTH
# =====================================================

@app.post("/api/register")
def register(req: UserAuthRequest):
    try:
        with db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (req.username,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username already exists")

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (req.username, req.password),
            )
            conn.commit()
            return {"status": "success", "message": "User registered successfully"}
    except HTTPException:
        raise
    except mysql.connector.Error as e:
        raise db_error(e)


@app.post("/api/login")
def login(req: UserAuthRequest):
    try:
        with db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (req.username, req.password),
            )
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=401, detail="Invalid username or password")
            return {"status": "success", "message": "Login successful", "user": user["username"]}
    except HTTPException:
        raise
    except mysql.connector.Error as e:
        raise db_error(e)


# =====================================================
# INVENTORY  (same rules as inventory.py)
# =====================================================

@app.get("/api/products")
def get_products():
    """Show all products, category wise."""
    try:
        with db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, category, price, stock FROM products ORDER BY category, name"
            )
            return cursor.fetchall()
    except mysql.connector.Error as e:
        raise db_error(e)


@app.post("/api/products")
def manual_add_product(p: ProductCreate):
    """Manual Add + Generate QR (inserts a NEW product, fails if the ID exists)."""
    try:
        with db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products(id,name,category,price,stock) VALUES(%s,%s,%s,%s,%s)",
                (p.id, p.name, p.category, p.price, p.stock),
            )
            conn.commit()
    except mysql.connector.Error as e:
        raise db_error(e)

    qr = make_qr(p.id, p.name, p.company, p.price, p.category)
    return {
        "status": "success",
        "message": f"Product added under '{p.category}'. QR saved as {p.id}.png",
        "qr": qr,
    }


@app.post("/api/products/scan")
def scan_add_product(p: ScanProduct):
    """Scan QR + Add: existing product gets stock added, unknown product is created."""
    if p.stock < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    try:
        with db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stock FROM products WHERE id=%s", (p.id,))
            result = cursor.fetchone()

            if result:
                new_stock = result[0] + p.stock
                cursor.execute("UPDATE products SET stock=%s WHERE id=%s", (new_stock, p.id))
                message = f"Stock updated. New stock = {new_stock}"
            else:
                cursor.execute(
                    "INSERT INTO products(id,name,category,price,stock) VALUES(%s,%s,%s,%s,%s)",
                    (p.id, p.name, p.category, p.price, p.stock),
                )
                message = f"New product added in '{p.category}' category"

            conn.commit()
            return {"status": "success", "message": message}
    except mysql.connector.Error as e:
        raise db_error(e)


@app.delete("/api/products/{pid}")
def remove_product(pid: int):
    try:
        with db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id=%s", (pid,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product Not Found")
            return {"status": "success", "message": "Product removed"}
    except HTTPException:
        raise
    except mysql.connector.Error as e:
        raise db_error(e)


# =====================================================
# BILLING  (same rules as billing.py)
#
# Each logged-in user has one open bill, kept in memory.
# Each bill line is [pid, name, category, price, qty, amount].
# Adding to the bill takes stock out of inventory right away, and
# removing / reducing puts it back, exactly like billing.py.
# =====================================================

carts = {}


def get_cart(user):
    return carts.setdefault(user, [])


def cart_response(user, **extra):
    cart = get_cart(user)
    return {"bill": cart, "grand_total": num(sum(i[5] for i in cart)), **extra}


@app.get("/api/cart/{user}")
def show_bill(user: str):
    return cart_response(user)


@app.post("/api/cart/{user}")
def add_to_bill(user: str, req: CartAdd):
    cart = get_cart(user)
    try:
        with db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, category, price, stock FROM products WHERE id=%s", (req.id,)
            )
            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail=f"No product found with ID {req.id}")

            name, category, price, stock = result[0], result[1], num(result[2]), result[3]

            if stock <= 0:
                raise HTTPException(status_code=400, detail=f"{name} is currently out of stock!")
            if req.qty <= 0:
                raise HTTPException(status_code=400, detail="Quantity must be at least 1")
            if req.qty > stock:
                raise HTTPException(
                    status_code=400, detail=f"Only {stock} items available in stock!"
                )

            amount = num(req.qty * price)
            cursor.execute(
                "UPDATE products SET stock=%s WHERE id=%s", (stock - req.qty, req.id)
            )
            conn.commit()
    except HTTPException:
        raise
    except mysql.connector.Error as e:
        raise db_error(e)

    # Same product added twice becomes one line with the quantities added together
    line = next((i for i in cart if i[0] == req.id), None)
    if line:
        line[4] += req.qty
        line[5] = num(line[5] + amount)
    else:
        cart.append([req.id, name, category, price, req.qty, amount])

    return cart_response(user, message=f"{req.qty} x {name} added to bill (\u20b9{amount})")


@app.post("/api/cart/{user}/remove")
def modify_bill(user: str, req: CartModify):
    """new_qty = the quantity to KEEP. 0 removes the product completely."""
    cart = get_cart(user)
    item = next((i for i in cart if i[0] == req.id), None)

    if item is None:
        raise HTTPException(status_code=404, detail="Product not found in bill")

    old_qty = item[4]
    if req.new_qty < 0 or req.new_qty > old_qty:
        raise HTTPException(
            status_code=400, detail=f"Enter a quantity between 0 and {old_qty}"
        )

    returned_qty = old_qty - req.new_qty

    try:
        with db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET stock = stock + %s WHERE id = %s", (returned_qty, req.id)
            )
            conn.commit()
    except mysql.connector.Error as e:
        raise db_error(e)

    if req.new_qty == 0:
        cart.remove(item)
        message = "Product removed successfully"
    else:
        item[4] = req.new_qty
        item[5] = num(req.new_qty * item[3])
        message = (
            f"Quantity updated successfully! New quantity: {req.new_qty}, "
            f"new amount: \u20b9{item[5]}"
        )

    return cart_response(user, message=message)


@app.post("/api/cart/{user}/clear")
def clear_bill(user: str):
    """Clear the bill. Stock for the cleared items goes back to inventory."""
    cart = get_cart(user)
    try:
        if cart:
            with db() as conn:
                cursor = conn.cursor()
                for item in cart:
                    cursor.execute(
                        "UPDATE products SET stock = stock + %s WHERE id = %s",
                        (item[4], item[0]),
                    )
                conn.commit()
    except mysql.connector.Error as e:
        raise db_error(e)

    carts[user] = []
    return cart_response(user, message="Bill cleared")


@app.post("/api/checkout/{user}")
def finish_bill(user: str):
    cart = get_cart(user)
    if not cart:
        raise HTTPException(status_code=400, detail="Bill is empty")

    try:
        with db() as conn:
            cursor = conn.cursor()
            try:
                # Next bill number is generated automatically
                cursor.execute("SELECT COALESCE(MAX(billno), 1000) + 1 FROM sales")
                billno = int(cursor.fetchone()[0])

                # Save all products under the same bill number
                for item in cart:
                    cursor.execute(
                        """
                        INSERT INTO sales
                        (billno, pid, name, category, qty, amount)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (billno, item[0], item[1], item[2], item[4], item[5]),
                    )
                conn.commit()
            except mysql.connector.Error:
                conn.rollback()
                raise
    except mysql.connector.Error as e:
        raise db_error(e)

    receipt = {
        "billno": billno,
        "date": datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"),
        "items": [list(i) for i in cart],
        "grand_total": num(sum(i[5] for i in cart)),
    }

    # Clear the current bill only after saving
    carts[user] = []
    return {"status": "success", "receipt": receipt}


# =====================================================
# SALES  (same reports as sales.py)
# =====================================================

@app.get("/api/sales")
def full_sales_report():
    try:
        with db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM sales ORDER BY billno DESC")
            return cursor.fetchall()
    except mysql.connector.Error as e:
        raise db_error(e)


@app.get("/api/sales/total")
def total_sales():
    try:
        with db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM sales")
            return {"total": num(cursor.fetchone()[0])}
    except mysql.connector.Error as e:
        raise db_error(e)


@app.get("/api/sales/category")
def category_sales():
    try:
        with db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT category, SUM(amount), COUNT(*) FROM sales GROUP BY category ORDER BY category"
            )
            return [
                {"category": r[0], "revenue": num(r[1]), "transactions": int(r[2])}
                for r in cursor.fetchall()
            ]
    except mysql.connector.Error as e:
        raise db_error(e)


@app.get("/api/sales/product")
def product_sales():
    try:
        with db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT category, name, SUM(amount) FROM sales GROUP BY category, name ORDER BY category, name"
            )
            return [
                {"category": r[0], "name": r[1], "amount": num(r[2])}
                for r in cursor.fetchall()
            ]
    except mysql.connector.Error as e:
        raise db_error(e)
