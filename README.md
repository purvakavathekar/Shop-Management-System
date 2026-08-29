# 🛒 Shop Management System

A desktop inventory, billing, and sales management application built with **Python**, **Tkinter**, and **MySQL**. The system streamlines retail operations by integrating item tracking, real-time sales reporting, and automated QR code generation/scanning for seamless checkout processing.

---

## ✨ Features

- 📦 **Inventory Control** — Full CRUD capability for store items with dynamic stock tracking
- 🔳 **QR Code Integration** — Automated QR code generation for products, with camera-based scanning via OpenCV & PyZbar
- 🧾 **Billing System** — Real-time cart calculation, itemized order summaries, and transaction logging
- 📊 **Sales Analytics** — Visual reporting powered by Pandas and Matplotlib to track performance and sales trends
- 🔐 **Secure Environment** — Environment variable protection using `python-dotenv` to safeguard database credentials

---

## 🧰 Tech Stack

| Category | Tools |
|---|---|
| Language | Python 3.x |
| GUI Framework | Tkinter |
| Database | MySQL |
| Computer Vision | OpenCV, PyZbar |
| Data & Visualization | Pandas, Matplotlib |
| Libraries | `mysql-connector-python`, `python-dotenv`, `qrcode` |

---

## 📁 Project Structure

```
Shop-Management-System/
│
├── .env                  # Database configuration (git-ignored)
├── .gitignore            # Git exclusion rules
├── db_connection.py      # Database connection handler
├── database.py           # Table initialization script
├── inventory.py          # Inventory management module
├── billing.py            # Checkout and scanner module
├── sales.py              # Reports and analytics module
├── qr_generator.py       # Standalone QR code generator
├── setup_database.sql    # SQL script to create DB + tables
├── sample_data.sql       # Optional sample data for testing
├── requirements.txt      # Python dependencies
└── main.py                # Main Tkinter application dashboard
```

---

## 🚀 Getting Started

### 1️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Set up the database
Open MySQL Workbench, connect to your local server, then run:
```
setup_database.sql
```
*(Optional)* Load sample data to test with:
```
sample_data.sql
```

### 3️⃣ Configure your credentials
Open `.env` and set your own MySQL password:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_NAME=shopproject
```
This file is git-ignored — your credentials stay local and never get pushed to GitHub. 🔒

### 4️⃣ Run the app
```bash
python main.py
```
This opens the main dashboard, from which you can launch **Inventory**, **Billing**, or **Sales Analysis**. 🎉

---

## 🖥️ How It Works

1. Add products manually or scan a QR code to auto-fill product details
2. Scan products at checkout — stock updates and bill total calculate in real time
3. Finalize the bill to log the sale to the database
4. Jump into **Sales Analysis** to view totals, top-selling products, and visual sales trends 📈

---

## 👩‍💻 Author

**Purva Kavathekar**