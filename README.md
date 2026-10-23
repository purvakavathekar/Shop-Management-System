# 🛒 Shop Management System (Web App)

A full-stack inventory, billing, and sales management web application. Originally built as a Python/Tkinter desktop application, it has been migrated to a modern web architecture with a **React (Vite)** frontend and a **FastAPI** backend, connected to a **MySQL** database.

The system streamlines retail operations by combining item tracking, sales reporting, and automatic QR code generation/scanning directly in the browser.

## 🌐 Live Demo

- **Frontend:** https://shop-management-system-1-t53a.onrender.com
- **Backend API:** https://shop-management-system-6avu.onrender.com

**Demo account:**

- Username: `demo`
- Password: `demo123`

> ⚠️ The backend runs on Render's free tier, which goes to sleep after 15 minutes of inactivity. The first request can take up to about 50 seconds while the server wakes up. If you see an error, wait a minute and try again.
>
> Please don't store anything sensitive in the demo; its data is public.

## ✨ Features

- 📦 **Inventory Control**: add, view, and delete store items with live stock tracking.
- 🔳 **QR Code Integration**: automatically generates a QR code for each new product and scans codes with the browser's webcam.
- 🧾 **Billing System**: cart with real-time totals, itemized order summaries, and transaction logging. Stock is updated when items are added to the cart and finalized at checkout.
- 📊 **Sales Analytics**: bar charts (Chart.js) for revenue by category and by product, plus a full sales history.
- 🔐 **Authentication**: login and registration system.
- 📱 **Responsive UI**: a modern purple-themed interface with custom modals that works on desktop and mobile.

## 🧰 Tech Stack

| Category  | Tools                                                    |
|-----------|----------------------------------------------------------|
| Frontend  | React, Vite, Axios, Chart.js (react-chartjs-2), html5-qrcode |
| Backend   | Python 3.x, FastAPI, Uvicorn, Pydantic                   |
| Database  | MySQL (hosted on Aiven Cloud)                            |
| Libraries | mysql-connector-python, python-dotenv, qrcode            |

## 📁 Project Structure

```
Shop - Management/
│
├── backend/                  # FastAPI backend
│   ├── qr_codes/             # Auto-generated QR code images are saved here
│   ├── ca.pem                # Aiven SSL certificate (optional, not required by the current code)
│   ├── database.py           # Creates the tables (also runs automatically on startup)
│   ├── db_connection.py      # Database connection handler (reads environment variables)
│   ├── main.py               # FastAPI application and all API routes
│   └── requirements.txt      # Backend dependencies
│
├── frontend/                 # React + Vite frontend
│   ├── public/
│   ├── src/                  # App.jsx, App.css, index.css, Login.jsx, main.jsx, etc.
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── .env                      # Database credentials (git-ignored, never commit this)
├── .gitignore
└── README.md
```

## 🚀 Getting Started (Local Development)

### 1️⃣ Set up the database

1. Create an empty database in MySQL, for example:
   ```sql
   CREATE DATABASE shopproject;
   ```
2. Create a `.env` file in the `backend` folder (or the project root) with your connection details:
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=shopproject
   ```
3. The tables (`products`, `sales`, `users`) are created automatically when the backend starts. You can also create them manually by running `python database.py` from the `backend` folder.

### 2️⃣ Start the backend (FastAPI)

```bash
cd backend
```

Activate a virtual environment:

- Windows: `python -m venv venv` then `venv\Scripts\activate`
- Mac/Linux: `python3 -m venv venv` then `source venv/bin/activate`

Install dependencies and run the server:

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 5000
```

The backend runs at `http://localhost:5000`.

### 3️⃣ Start the frontend (React + Vite)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

> **Note:** the frontend currently points to the deployed backend. To use your local backend, change the `API` constant near the top of `frontend/src/App.jsx` from the Render URL to `http://localhost:5000`.

## ☁️ Deployment Guide (Render + Aiven)

### Database (Aiven MySQL)

1. Create a MySQL service on Aiven and note the host, **port**, user, password and database name from the Connection information panel. Aiven uses a custom port, not 3306.
2. In the service settings, make sure **Allowed IP addresses** includes `0.0.0.0/0` (Render's outbound IPs change).

### Backend (Render Web Service)

1. Create a **Web Service** on Render and connect your GitHub repository.
2. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Add these **Environment Variables**:

   | Key           | Value                                  |
   |---------------|----------------------------------------|
   | `DB_HOST`     | your Aiven host                        |
   | `DB_PORT`     | your Aiven port (for example `11342`)  |
   | `DB_USER`     | `avnadmin`                             |
   | `DB_PASSWORD` | your Aiven password                    |
   | `DB_NAME`     | `defaultdb`                            |

4. On the first start, the backend creates the tables automatically. Check the logs for `Database Ready inside target database!`.

### Frontend (Render Static Site)

1. Create a **Static Site** on Render and connect the same repository.
2. Settings:
   - **Root Directory:** leave blank
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/dist`

## 🖥️ How It Works

1. **Login / Register:** open the app and create an account.
2. **Manage Inventory:** add products manually (the backend generates a `.png` QR code) or scan an existing QR code with your webcam.
3. **Billing:** scan products or add them manually. The cart updates instantly.
4. **Checkout:** finalize the bill to save it to the database and generate a digital receipt. Bill numbers are generated automatically.
5. **Analytics:** open the Sales page to see total revenue, category breakdowns, and bar charts.

## 🔒 Security Notes

- Never commit your `.env` file or database password to GitHub. Keep `.env` in `.gitignore`.
- Passwords are currently stored as plain text in the `users` table. Before real-world use, hash them (for example with `bcrypt`).
- CORS is currently open to all origins. For production, restrict `allow_origins` in `main.py` to your frontend URL.

## 👩‍💻 Author

Purva Kavathekar
