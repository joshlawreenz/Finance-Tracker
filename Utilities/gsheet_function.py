import pandas as pd
import re
import gspread
from google.oauth2.service_account import Credentials

def get_googlesheet_df():
    # -------------------------------------------------------
    # CONFIG
    # -------------------------------------------------------
    SERVICE_ACCOUNT_FILE = "service_account.json"  # Your JSON key
    SPREADSHEET_NAME = "Credit Statement Breakdown"
    WORKSHEET_NAME = "Copy of EASTWEST"   # The worksheet you want to fetch
    OUTPUT_FILE = "cleaned.csv"

    # -------------------------------------------------------
    # AUTHENTICATE WITH GOOGLE SHEETS
    # -------------------------------------------------------
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

    # -------------------------------------------------------
    # FETCH SHEET DATA
    # -------------------------------------------------------
    print(f"Fetching data from Google Sheet: {SPREADSHEET_NAME}/{WORKSHEET_NAME}")
    rows = ws.get_all_values()[1:]  # returns list of lists

    # -------------------------------------------------------
    # Helpers
    # -------------------------------------------------------
    def is_header(row):
        if not row:
            return False
        return row[0].strip().lower() == "date"

    def is_empty_row(row):
        return all(str(x).strip() == "" for x in row)

    def has_peso(row):
        return any("₱" in str(x) for x in row)

    def extract_month(date_str):
        m = re.match(r"([A-Za-z]+)", date_str)
        return m.group(1) if m else None

    def extract_day(date_str):
        m = re.search(r"(\d+)", date_str)
        return m.group(1) if m else None

    # -------------------------------------------------------
    # CLEAN 1: Remove empty rows + repeated headers
    # -------------------------------------------------------
    cleaned_rows = []
    for row in rows:
        if is_empty_row(row):
            continue
        if is_header(row):
            continue
        cleaned_rows.append(row)

    # -------------------------------------------------------
    # CLEAN 2: Handle blocks + reversal + month application
    # -------------------------------------------------------
    blocks = []
    current_block = []
    current_month = None
    last_date = None  # Track last seen date (full string)

    for row in cleaned_rows:
        date_raw = row[0].strip()

        if date_raw:  # Not empty
            month_in_row = extract_month(date_raw)
            day_in_row = extract_day(date_raw)

            if month_in_row:
                # Full date like "May 03"
                current_month = month_in_row
                last_date = date_raw
            elif day_in_row and current_month:
                # Numeric day only → prepend current month
                date_fixed = f"{current_month} {day_in_row}"
                row[0] = date_fixed
                last_date = date_fixed
            else:
                # Anything else, just keep as-is
                last_date = date_raw
        else:
            # Empty date → inherit last_date
            if last_date:
                row[0] = last_date

        # Handle block ending on Peso
        if has_peso(row):
            if current_block:
                blocks.append(current_block[::-1])
            current_block = []
        else:
            current_block.append(row)

    # Add last block
    if current_block:
        blocks.append(current_block[::-1])

    # -------------------------------------------------------
    # CLEAN 3: Flatten blocks into final list
    # -------------------------------------------------------
    final_rows = [r for block in blocks for r in block]

    # -------------------------------------------------------
    # CLEAN 4: Convert numeric columns
    # -------------------------------------------------------
    columns = ["Date", "Description", "CREDIT", "JOSH", "ZARAH", "MOTHER", "MERRIEL", "OTHERS", "Remarks"]
    df = pd.DataFrame(final_rows, columns=columns)
    for col in df.columns[2:-1]:  # exclude Date, Description, and Remarks
        # Convert to string, remove commas, handle parentheses
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)             # remove commas
            .str.replace(r"\((.*?)\)", r"-\1", regex=True) # (100) → -100
            .replace("", "0")                               # empty → 0
            .astype(float)
        )
    # Reset index properly and return
    df.reset_index(drop=True, inplace=True)
    return df
