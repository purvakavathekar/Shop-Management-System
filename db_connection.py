# -*- coding: utf-8 -*-
"""
Created on Sat Aug 29 23:18:16 2026

@author: rahul
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load variables from the .env file
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "purva@123"
DB_NAME = "shopproject"


def get_connection(use_database=True):
    if not DB_PASSWORD:
        raise RuntimeError(
            "DB_PASSWORD is missing. Check your .env file."
        )

    try:
        if use_database:
            con = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
            )
        else:
            con = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
            )
        return con

    except Error as e:
        print(f"[Database Error] Could not connect to MySQL: {e}")
        sys.exit(1)