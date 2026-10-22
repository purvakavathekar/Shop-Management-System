# -*- coding: utf-8 -*-
import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load variables from local .env file
load_dotenv()

# Read from environment variables (fallback to defaults if developing locally)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 11342))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "defaultdb")


def get_connection(use_database=True):
    if not DB_PASSWORD:
        raise RuntimeError(
            "DB_PASSWORD is missing. Check your .env file or Render Environment Variables."
        )

    try:
        connection_config = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "ssl_disabled": False  # Required for Aiven SSL connections
        }

        if use_database:
            connection_config["database"] = DB_NAME

        con = mysql.connector.connect(**connection_config)
        return con

    except Error as e:
        print(f"[Database Error] Could not connect to MySQL: {e}")
        raise e