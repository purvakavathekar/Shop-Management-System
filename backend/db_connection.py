# -*- coding: utf-8 -*-
import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

# Read dynamic values set on Render
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "11342"))  # Explicitly cast to integer
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "defaultdb")


def get_connection(use_database=True):
    if not DB_PASSWORD:
        raise RuntimeError(
            "DB_PASSWORD is missing. Check your Render Environment Variables."
        )

    try:
        connection_config = {
            "host": DB_HOST,
            "port": DB_PORT,             # Connects to 11342 instead of 3306
            "user": DB_USER,
            "password": DB_PASSWORD,
            "connection_timeout": 10,
            "ssl_mode": "REQUIRED"
        }

        if use_database:
            connection_config["database"] = DB_NAME

        return mysql.connector.connect(**connection_config)

    except Error as e:
        print(f"[Database Error] Connection failed: {e}")
        raise e