import streamlit as st
import pandas as pd
import numpy as np
from Utilities.gsheet_function import get_googlesheet_df
import re
from datetime import datetime
import calendar

now = datetime.now()

# if now.day in range(1,3) and now.day in :
#     index_month = now.strftime("%B").upper()
# else:
#     previous_month = now.month
#     index_month = calendar.month_name[previous_month].upper()
# print(index_month)

st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💳",
    layout="centered",
    initial_sidebar_state="auto"
)
st.title("💳 Credit Card Spending Tracker")

df = get_googlesheet_df()
# -------------------------------------------------------
# Convert numeric columns (remove commas, coerce to float)
# -------------------------------------------------------
for col in df.columns[2:-1]:  # assuming first 2 columns are Date, Description, last is Remarks
    df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "", regex=False), errors="coerce").fillna(0)

# -------------------------------------------------------
# Convert 'Date' to datetime
# -------------------------------------------------------
current_year = pd.Timestamp.now().year
df['Date_dt'] = pd.to_datetime(df['Date'] + f" {current_year}", format="%B %d %Y")

def override_month(row):
    if pd.isna(row['Remarks']):
        return None
    match = re.search(r"Include for (\w+)", row['Remarks'])
    if match:
        return match.group(1)
    return None

df['OverrideMonth'] = df.apply(override_month, axis=1)

# Create datetime column for filtering
def compute_date(row):
    if pd.notna(row['OverrideMonth']):
        return pd.to_datetime(f"{row['OverrideMonth']} 01 {current_year}", format="%B %d %Y")
    else:
        return pd.to_datetime(f"{row['Date']} {current_year}", format="%B %d %Y", errors='coerce')

df['Date_dt'] = df.apply(compute_date, axis=1)

# -------------------------------------------------------
# Generate cutoff periods (3rd → 2nd of next month)
# -------------------------------------------------------
cutoffs = []
for month in range(1, 13):
    start = pd.Timestamp(year=current_year, month=month, day=3)
    if month == 12:
        end = pd.Timestamp(year=current_year + 1, month=1, day=2)
    else:
        end = pd.Timestamp(year=current_year, month=month+1, day=2)
    cutoffs.append((start, end))
# Streamlit dropdown
# cutoff_labels = [f"{start.strftime('%b %d')} - {end.strftime('%b %d')}" for start, end in cutoffs]
cutoff_labels = [f"{end.strftime('%B')}".upper() for start,end in cutoffs]
print(cutoffs)
# Get month to display depending on current date
# now = now = datetime.now()

if now.day >= 3:
    index_month = now.month - 1
else:
    index_month = now.month

print(index_month)
selected_index = st.selectbox("Select Statement Period", range(len(cutoffs)), format_func=lambda x: cutoff_labels[x], index=index_month)

start, end = cutoffs[selected_index]

# Filter DataFrame for selected cutoff
df_cutoff = df[(df['Date_dt'] >= start) & (df['Date_dt'] <= end)]
df_cutoff = df_cutoff.drop(columns=['Date_dt'])

df_display = df_cutoff.copy()
df_display = df_display[~df_display['Remarks'].str.contains("Hide", case=False, na=False)]
# -------------------------------------------------------
# Streamlit Display
# -------------------------------------------------------
st.set_page_config(page_title="Finance Tracker", layout="wide")
st.title("Finance Tracker")

# Transactions table (hide index)
st.subheader(f"Transactions from {start.strftime('%b %d')} to {end.strftime('%b %d')}")
st.dataframe(df_display, use_container_width=True, hide_index=True)

# Totals per numeric column
st.subheader("Totals for selected cutoff")
totals = df_display.iloc[:, 2:8].sum()  # numeric columns only
st.table(totals)

# Optional: filter by description
desc_filter = st.text_input("Filter by Description (optional)")
if desc_filter:
    filtered_desc = df_display[df_display['Description'].str.contains(desc_filter, case=False)]
    st.subheader(f"Filtered by '{desc_filter}'")
    st.dataframe(filtered_desc, use_container_width=True, hide_index=True)
# # -------------------------------------------------------
# # Streamlit UI
# # -------------------------------------------------------
# st.set_page_config(page_title="Finance Tracker", layout="wide")
# st.title("💰 Finance Tracker")

# # Filter by Date
# unique_dates = sorted(df['Date'].unique(), reverse=True)

# selected_date = st.selectbox("Select Date", unique_dates, index=0)
# filtered_df = df[df['Date'] == selected_date]

# # Display transactions table
# st.subheader(f"Transactions on {selected_date}")
# st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# # Show totals
# st.subheader("Totals for selected date")
# totals = filtered_df.iloc[:, 2:-1].sum()  # sum numeric columns only
# st.table(totals)

# # Optional: filter by Description
# desc_filter = st.text_input("Filter by Description (optional)")
# if desc_filter:
#     filtered_desc = filtered_df[filtered_df['Description'].str.contains(desc_filter, case=False)]
#     st.subheader(f"Filtered by '{desc_filter}'")
#     st.dataframe(filtered_desc, use_container_width=True)