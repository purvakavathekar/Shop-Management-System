# 🛒 Shop Management System (Web App)

A full-stack inventory, billing, and sales management web application. Originally built as a Python/Tkinter desktop application, it has been migrated to a modern web architecture featuring a **React (Vite)** frontend and a **FastAPI** backend, connected to a **MySQL** database. 

The system streamlines retail operations by integrating item tracking, real-time sales reporting, and automated QR code generation/scanning directly in the browser.

---

## ✨ Features

- 📦 **Inventory Control** — Full CRUD capability for store items with dynamic stock tracking.
- 🔳 **QR Code Integration** — Automatically generates QR codes for new products (saved in the backend) and uses the browser's webcam to scan them seamlessly.
- 🧾 **Billing System** — Real-time cart calculation, itemized order summaries, and transaction logging. Stock is deducted immediately upon scanning.
- 📊 **Sales Analytics** — Interactive visual reporting powered by Chart.js to track performance, category revenue, and sales trends.
- 🔐 **Authentication** — Secure Login and Registration system.
- 📱 **Responsive UI** — A modern, dark-themed web interface with custom modals.

---

## 🧰 Tech Stack

| Category | Tools |
|---|---|
| **Frontend** | React.js, Vite, Axios, Chart.js, `html5-qrcode` |
| **Backend** | Python 3.x, FastAPI, Uvicorn, Pydantic |
| **Database** | MySQL |
| **Libraries** | `mysql-connector-python`, `python-dotenv`, `qrcode` |

---

## 📁 Project Structure

```text
Shop - Management/
│
├── backend/                  # FastAPI Backend
│   ├── __pycache__/          
│   ├── qr_codes/             # Auto-generated QR code images saved here
│   ├── venv/                 # Python virtual environment
│   ├── database.py           # Table initialization script
│   └── main.py               # FastAPI application & all API routes
│
├── frontend/                 # React + Vite Frontend
│   ├── node_modules/
│   ├── public/
│   ├── src/                  # Contains App.jsx, App.css, index.css, etc.
│   ├── .gitignore
│   ├── .oxlintrc.json
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── README.md
│   └── vite.config.js
│
├── .env                      # Database credentials (git-ignored)
├── .gitignore                # Git exclusion rules
├── billing.py                # (Legacy) Desktop billing module
├── inventory.py              # (Legacy) Desktop inventory module
├── sales.py                  # (Legacy) Desktop sales module
├── main.py                   # (Legacy) Main Tkinter dashboard
├── qr_generator.py           # Standalone QR code generator script
└── README.md
🚀 Getting Started
1️⃣ Set up the Database
Open MySQL Workbench (or your MySQL command line).

Connect to your local server and run the database.py script (located in the backend folder) to create the shopproject database and necessary tables (products, sales, users).

Ensure your .env file in the root directory has the correct MySQL password.

2️⃣ Start the Backend (FastAPI)
Open a terminal and navigate to the backend folder:

bash
cd backend
Activate your virtual environment:

Windows: venv\Scripts\activate

Mac/Linux: source venv/bin/activate

Install dependencies and run the server:

bash
pip install fastapi uvicorn mysql-connector-python python-dotenv pydantic qrcode
python -m uvicorn main:app --reload --port 5000
The backend will run at http://localhost:5000.

3️⃣ Start the Frontend (React + Vite)
Open a second terminal and navigate to the frontend folder:

bash
cd frontend
Install the required packages and start the dev server:

bash
npm install
npm run dev
The frontend will run at http://localhost:5173.

🖥️ How It Works
Login/Register: Open http://localhost:5173 in your browser and create an account or log in.

Manage Inventory: Add products manually (the backend generates a .png QR code saved in the qr_codes folder) or scan an existing QR code using your webcam.

Billing: Scan products or add them manually. The cart updates instantly, and stock is reserved.

Checkout: Finalize the bill to log it to the database and generate a digital receipt. Bill numbers are automatically generated.

Analytics: Jump into the Sales Analysis dashboard to view total revenue, category breakdowns, and interactive bar charts.

👩‍💻 Author
Purva Kavathekar