import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
import st_yled
import time

from Utilities.gsheet_functionv2 import *
from Utilities.dframe_utility import *

now = datetime.now()

SERVICE_ACCOUNT_FILE = "service_account.json"
PESO_ICON = "assets/gold_peso.svg"
HOME_ICON = "assets/home_icon.png"
LOGO_ICON = "assets/long_logo.svg"
EW_LOGO = "assets/ew_long_logo.svg"
RCBC_LOGO = "assets/rcbc_logo.svg"
BPI_LOGO = "assets/bpi_logo.svg"

def display_logo(bank):
    if bank == "EASTWEST":
        st.image(EW_LOGO,width=400)
    elif bank == "RCBC":
        st.image(RCBC_LOGO,width=150)
    elif bank == "BPI":
        st.image(BPI_LOGO,width=150)
        

# Initialize styling - set for each app page
st_yled.init()

st.set_page_config(
    page_title="CardSpend Monitor",
    page_icon=PESO_ICON,
    layout="wide",
    initial_sidebar_state="auto" #"collapsed" later
)
st.title("CardSpend Monitor")
st.logo(
    LOGO_ICON,
    # link="https://streamlit.io/gallery",
    icon_image=PESO_ICON,
    size="large"
)

# Using "with" notation
with st.sidebar:
    st.button("Home", type="tertiary", icon=":material/home:")
    refresh = st.button("Refresh", type="tertiary", icon=":material/restart_alt:")

    if refresh:
        st.rerun()
    # st.button("Placeholder", type="tertiary", icon=":material/restart_alt:")
    st.divider()

# Google Sheet
# df = get_googlesheet_df()
df = load_sheet()

# Removes FINAL TOTAL column
hide_columns = ['FINAL TOTAL','INSTALLMENT','STATUS']

df = df[::-1]

borrowers = default_borrowers = get_borrowers_list(df)
# bank_list = get_bank_list(df)

months_capitalized = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

bank_list = ['EASTWEST','RCBC', 'BPI']
bank_list_colored = [':violet[EASTWEST]',':blue[RCBC]',':red[BPI]']

# Get Total Amount Spent
sidebar_total_amount = get_total_amount_spent(df,borrowers=borrowers)

if "filter_name" not in st.session_state:
    borrowers = [i.upper() for i in borrowers]
    st.session_state["filter_name"] = borrowers
else:
    borrowers = st.session_state.filter_name

#-------------#
### MAIN PAGE
eastwest, rcbc, bpi = st.tabs(bank_list_colored,default=':violet[EASTWEST]')
tab_list = [eastwest,rcbc,bpi]

df_display = df.copy()

try:
    df_display.drop(hide_columns, inplace=True, axis=1)
except KeyError:
    pass

# Change date format of display df
df_display["DATE"] = pd.to_datetime(df["DATE"])
df_display["DATE"] = df_display["DATE"].dt.strftime("%B %d, %Y")

bank_image = [EW_LOGO,RCBC_LOGO,BPI_LOGO]

# Generates JSON bank details
bank_details_list = generate_bank_details(bank_list)

### Bank Tabs
index = 0
for tab in tab_list:
    with tab:
        bank = bank_list[index]
        breakdown = get_total_amount_spent(df_display,borrowers,bank)
        bank_df = df_display[df_display["BANK"] == bank]

        logo_col,breakdown_col,totalamount_col = st.columns([0.25,0.25,0.34],vertical_alignment='center')

        # Displays the bank logo, has strict sizes so SVG editing is needed
        with logo_col:
            display_logo(bank)
            default_borrowers = [i.capitalize() for i in default_borrowers]

            statementdate_col,filter_col,  = st.columns(2,vertical_alignment='top')

            with filter_col:
                # Allows User filtering
                filter_options = st.pills(
                    "Select borrowers to display", 
                    default_borrowers, 
                    selection_mode="multi",
                    key=bank,
                    default=default_borrowers,
                    label_visibility="visible"
                    )
                borrowers = filter_options
                
            with statementdate_col:
                statement_month = st.selectbox('Select Statement Period',label_visibility='visible',options=months_capitalized,key=bank+'statement',index=now.month-1)

        st.subheader("Transactions")
        # Apply borrower filter to dataframe
        bank_borrowers = [i.upper() for i in borrowers]
        bank_df = bank_df[bank_df["BORROWER"].isin(bank_borrowers)]

        # Sort transactions based on date
        bank_df["DATE"] = pd.to_datetime(bank_df["DATE"])
        bank_df = bank_df.sort_values("DATE", ascending=False)
        bank_df["DATE"] = bank_df["DATE"].dt.strftime("%B %d, %Y")

        # Filters to current cutoff
        current_year = now.strftime("%Y").upper()

        # EASTWEST & RCBC
        if statement_month:
            # statement_month
            month_int = datetime.strptime(f"{statement_month} 1, 1900",'%B %d, %Y').month
        if now.day in range(1,3):
            pass
        else:
            month_int = month_int + 1

        if bank in ['EASTWEST','RCBC']:
            if month_int > 12:
                month_res = month_int - 12
                cutoff_enddate = datetime(int(current_year), abs(int(month_res)), 2) + relativedelta(years=1)
                cutoff_startdate = cutoff_enddate - relativedelta(months=1) + relativedelta(days=1)
            else:
                cutoff_enddate = datetime(int(current_year), int(month_int), 2)
                cutoff_startdate = cutoff_enddate - relativedelta(months=1) + relativedelta(days=1)
        elif bank == 'BPI':
            if month_int > 12:
                month_res = month_int - 12
                cutoff_enddate = datetime(int(current_year), abs(int(month_res)), 13) + relativedelta(years=1)
                cutoff_startdate = cutoff_enddate - relativedelta(months=1) + relativedelta(days=1)
            else:
                cutoff_enddate = datetime(int(current_year), int(month_int), 13)
                cutoff_startdate = cutoff_enddate - relativedelta(months=1) + relativedelta(days=1)


        bank_df["DATE"] = pd.to_datetime(bank_df["DATE"])
        bank_df = bank_df[(bank_df["DATE"] >= cutoff_startdate) & (bank_df["DATE"] <= cutoff_enddate)]
        bank_df["DATE"] = bank_df["DATE"].dt.strftime("%B %d, %Y")

        # Reduces date redundancy
        bank_df["DATE"] = bank_df["DATE"].mask(bank_df["DATE"].duplicated(), "")

        # Dataframe Config
        bankdf_config = {
                        "DATE": st.column_config.Column(
                            width="small"
                        ),
                        "DESCRIPTION": st.column_config.Column(
                            width="large"
                        ),
                        "AMOUNT": st.column_config.NumberColumn(
                            format="₱ %.2f",
                            width="medium"
                        )
                    }
        
        st.dataframe(bank_df,width="stretch",hide_index=True, column_config=bankdf_config)

        # Breakdown Column
        with breakdown_col:
            st.subheader("Breakdown")
            breakdown = get_total_amount_spent(df_display,borrowers,bank,start=cutoff_startdate,end=cutoff_enddate)
            # Dataframe Config
            breakdown_config = {
                            "Total": st.column_config.NumberColumn(
                                format="₱ %.2f",
                                width="medium"
                            )
                        }
            st.dataframe(breakdown,hide_index=True,column_config=breakdown_config)

        # Transaction Metric (WIP)
        with totalamount_col:
            string = bank_details_list[index].get('total_amount_string')
            monthly_due = get_monthly_due(df_display,bank,start=cutoff_startdate,end=cutoff_enddate)


            st.metric(string, 
                        "₱" + str(f"{monthly_due:.2f}"),
                        # abs(monthly_due/2 - monthly_due),
                        " ",
                        chart_data=[0,monthly_due/2,monthly_due,monthly_due/2], 
                        chart_type="area",
                        border=True,
                        )

        index += 1
        translist_col,col2,col3,transmodifier_col = st.columns([0.5,0.15,0.5,0.15],vertical_alignment="center",border=False)

        ## Transaction Modifiers
        # Add Transaction Modal
        with transmodifier_col:
            @st.dialog("Add Transaction",on_dismiss="rerun")
            def add_transaction():
                st.divider()
                date_col,unlock_col,amount_col = st.columns([0.45,0.05,0.60],vertical_alignment="bottom")
                date_disabled_state = True

                # Lock icon Column
                if unlock_col.button(":material/lock_open:",type='tertiary',help='Unlock date'):
                    date_disabled_state = False

                # Date Column
                date_of_transaction = date_col.date_input("Date", "today",disabled=date_disabled_state)

                # Amount Column
                amount = amount_col.number_input("Amount",value=None,icon=":material/currency_ruble:")
                
                # User and Bank Column
                user_col, bank_col = st.columns(2)
                transaction_borrower = user_col.multiselect('Card User/s',options=default_borrowers,default="Josh")
                bank_selection = bank_col.selectbox('Bank',options=bank_list)
                
                # Text Columns
                description = st.text_input("Description",max_chars=50)
                remarks_check = st.checkbox('Remarks')

                remarks = None
                if remarks_check:
                    remarks = st.text_area('Remarks',label_visibility="collapsed",max_chars=100)
                
                # Installment Columns
                installment_check_col, installment_drop = st.columns(2)
                installment_check = installment_check_col.checkbox('Installment terms')
                installment_selection = None
                if installment_check:
                    installment_selection = installment_drop.selectbox(
                        "Terms",
                        ['3 Months','6 months', '9 months', '12 months', '18 months'],
                        placeholder='Payment Terms',
                        label_visibility="collapsed"
                    )

                # Bottom Modal Columns
                col1,col2,button_col = st.columns([0.70,0.10,0.20],vertical_alignment="bottom")

                # Submit button Column
                if button_col.button("Submit"):
                    # Makes user fill-up required fields
                    if not (amount 
                            and description 
                            and bank_selection 
                            and date_of_transaction
                            and transaction_borrower):
                        st.warning('Please fill up required fields.')
                    else:
                        # Spinner loader
                        with st.spinner("Submitting...", show_time=False):
                            # Generates multiple entries based on installment terms
                            file_path = "output.csv"
                            write_header = not os.path.exists(file_path) or os.path.getsize(file_path) == 0

                            # transaction_borrower = ",".join(transaction_borrower).upper()
                            if installment_check:
                                row_list = []
                                monthly_term, x = installment_selection.split(" ")
                                divided_amount = amount / float(monthly_term)
                                initial_date_of_transaction = date_of_transaction

                                # If multiple users are selected, loop the users
                                if len(transaction_borrower) > 1:
                                    divided_amount = divided_amount/len(transaction_borrower)
                                    for borrower in transaction_borrower:
                                        date = initial_date_of_transaction
                                        for i in range(int(monthly_term)):
                                            suffix = f" ({i+1}/{monthly_term})"
                                            new_row = {
                                                "DATE": date,
                                                "DESCRIPTION": description + suffix,
                                                "BANK": bank_selection.upper(),
                                                "BORROWER": borrower.upper(),
                                                "AMOUNT": float(divided_amount),
                                                "INSTALLMENT": installment_selection,
                                                "REMARKS": remarks
                                            }
                                            # Adds 1 month to date per installment
                                            date = date + relativedelta(months=1)
                                            row_list.append(new_row)
                                else:
                                    for i in range(int(monthly_term)):
                                        suffix = f" ({i+1}/{monthly_term})"
                                        new_row = {
                                            "DATE": date_of_transaction,
                                            "DESCRIPTION": description + suffix,
                                            "BANK": bank_selection.upper(),
                                            "BORROWER": transaction_borrower[0].upper(),
                                            "AMOUNT": float(divided_amount),
                                            "INSTALLMENT": installment_selection,
                                            "REMARKS": remarks
                                        }
                                        # Adds 1 month to date per installment
                                        date_of_transaction = date_of_transaction + relativedelta(months=1)
                                        row_list.append(new_row)

                                df_new = pd.DataFrame(row_list)
                                
                                write_header = not os.path.exists(file_path) or os.path.getsize(file_path) == 0
                                df_new.to_csv(file_path, mode="a",header=write_header,index=False)
                            else:
                                if len(transaction_borrower) > 1:
                                    transaction_list = []
                                    amount = amount/len(transaction_borrower)
                                    for borrower in transaction_borrower:
                                        new_row = {
                                            "DATE": date_of_transaction,
                                            "DESCRIPTION": description,
                                            "BANK": bank_selection.upper(),
                                            "BORROWER": borrower.upper(),
                                            "AMOUNT": float(amount),
                                            "INSTALLMENT": None,
                                            "REMARKS": remarks
                                        }
                                        transaction_list.append(transaction_list)
                                else:
                                    new_row = {
                                        "DATE": date_of_transaction,
                                        "DESCRIPTION": description,
                                        "BANK": bank_selection.upper(),
                                        "BORROWER": transaction_borrower[0].upper(),
                                        "AMOUNT": float(amount),
                                        "INSTALLMENT": None,
                                        "REMARKS": remarks
                                    }
                                    transaction_list = [new_row]
                                df_new = pd.DataFrame(transaction_list)
                                df_new.to_csv(file_path, mode="a",header=write_header,index=False)

                            # with st.spinner("Submitting...", show_time=False):
                            time.sleep(1.2)
                        st.success('Transaction submitted!', icon="✅")
                        st.rerun()
                
            if st.button("Add Transaction",key=bank+'add'):
                add_transaction()


### SIDEBAR FOOTER
with st.sidebar:
    st_yled.title("Top Spenders of the Month 💵",font_size="20.0px")
    top_spender = sidebar_total_amount

    # Rank Spenders
    count = 1
    for i in top_spender:
        i.update({"rank":count})
        count += 1

    col1, col2= st.columns(2,gap="large")
    with col1:
        count = 1
        for spender in top_spender:
            spender = spender["Name"]
            if spender == 'Zarah':
                spender = "<span style='color: #F88379'>Zarah</span>"
            string = f"## {count}. {spender}</span>"
            if count == 1:
                string = string + "  🎉</span>"

            st.markdown(string, 
                unsafe_allow_html=True
            )
            count += 1
    with col2:
        for spender in top_spender:
            st.markdown(f"## <span style='color: #AFED32'>₱ {spender["Total"]}</span>", 
                unsafe_allow_html=True
            )

    index = []
    count = 1
    for i in range(len(top_spender)):
        index.append(count)
        count += 1

    # Side bar footer message
    # # Cleanly adjust spacing
    space=0
    while space < 2:
        st.space(size="medium")
        space +=1
    st.space(size="small")
    st.divider()
    st_yled.caption("Hey there!",font_size="11.0px")
    st_yled.caption("This is my personal spending tracker which is currently synced to my Google Sheets account.",font_size="11.0px")
    st_yled.link_button(":green[Google Sheet]", "https://docs.google.com/spreadsheets/d/1qFQco0hOYwg8_SYcqj_kDXcdb_Gf9GKtlnU1ok4nok8/edit?pli=1&gid=1924750089#gid=1924750089",type="tertiary",font_size="13.0px")
    st_yled.caption("This is still a work in progress.",font_size="11.0px")
    st_yled.caption("## Josh V. " + "૮ ･ ﻌ･ა",font_size="11.0px")
    st.divider()
    st.write(f"{datetime.now().strftime("%A | %B %d, %Y")}")

# df = st.dataframe(df, width="stretch", hide_index=True)
# st_yled.table(df, background_color="#041d36", color="#d5d9dd",border_style="solid")
