import pandas as pd
import os
import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = "service_account.json"  # Your JSON key
SPREADSHEET_NAME = "Credit Statement Breakdown"
WORKSHEET_NAME = "Prototype"   # The worksheet you want to fetch
OUTPUT_FILE = "cleaned.csv"

def load_sheet():
    if os.path.exists("local_sheet_backup.csv"):
        df = pd.read_csv("local_sheet_backup.csv",skiprows=12)
        return df
    else:
        raise("No sheets found.")
    
def get_googlesheet_df():
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=scopes
    )
    gc = gspread.authorize(creds)
    sh = gc.open(SPREADSHEET_NAME)
    ws = sh.worksheet(WORKSHEET_NAME)

    rows = ws.get_all_values()[12:]

    # Get Headers
    header = rows[0]

    df = pd.DataFrame(rows[1:], columns=header)
    return df