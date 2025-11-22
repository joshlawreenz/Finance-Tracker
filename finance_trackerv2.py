import streamlit as st
from datetime import datetime
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
bank_list = ['EASTWEST','RCBC', 'BPI']
bank_list_colored = [':violet[EASTWEST]',':blue[RCBC]',':red[BPI]']

# Get Total Amount Spent
sidebar_total_amount = get_total_amount_spent(df,borrowers)

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
df_display.drop(hide_columns, inplace=True, axis=1)

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
        monthly_due = get_monthly_due(df_display,bank)

        logo_col,breakdown_col,totalamount_col = st.columns([0.25,0.25,0.34],vertical_alignment='center')

        # Displays the bank logo, has strict sizes so SVG editing is needed
        with logo_col:
            display_logo(bank)
            default_borrowers = [i.capitalize() for i in default_borrowers]

            # Allows User filtering
            filter_options = st.pills(
                "Filter", 
                default_borrowers, 
                selection_mode="multi",
                key=bank,
                default=default_borrowers
                )
            borrowers = filter_options

        # Breakdown Column
        with breakdown_col:
            st.subheader("Breakdown")
            st.dataframe(breakdown,hide_index=True)

        # Transaction Metric (WIP)
        with totalamount_col:
            string = bank_details_list[index].get('total_amount_string')
            st.metric(string, 
                        "₱" + str(f"{monthly_due:.2f}"),
                        # abs(monthly_due/2 - monthly_due),
                        " ",
                        chart_data=[0,monthly_due/2,monthly_due,monthly_due/2], 
                        chart_type="area",
                        border=True,
                        )
        translist_col,transmodifier_col = st.columns([0.6,0.4],vertical_alignment="top",border=True)

        # Transaction List (Dataframe)
        with translist_col:
            st.subheader("Transactions")
            # Filters borrowers
            bank_borrowers = [i.upper() for i in borrowers]
            bank_df = bank_df[bank_df["BORROWER"].isin(bank_borrowers)]

            # Sort transactions based on date
            bank_df["DATE"] = pd.to_datetime(bank_df["DATE"])
            bank_df = bank_df.sort_values("DATE", ascending=False)
            bank_df["DATE"] = bank_df["DATE"].dt.strftime("%B %d, %Y")

            # Reduces date redundancy
            bank_df["DATE"] = bank_df["DATE"].mask(bank_df["DATE"].duplicated(), "")

            st.dataframe(bank_df, width="stretch", hide_index=True)

            index += 1

        # Transaction Modifiers
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
                transaction_borrower = user_col.multiselect('Card User/s',options=default_borrowers)
                bank_selection = bank_col.selectbox('Bank',options=bank_list)
                
                # Text Columns
                description = st.text_input("Description")
                
                remarks = st.text_area('Remarks')
                
                # Installment Columns
                installment_check_col, installment_drop = st.columns(2)
                installment_check = installment_check_col.checkbox('Installment?')
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
                    with st.spinner("Submitting...", show_time=False):
                    # Generates multiple entries based on installment terms
                        if installment_check:
                            installment_selection

                            new_row = {
                                "DATE": date_of_transaction,
                                "DESCRIPTION": description,
                                "BANK": bank_selection.upper(),
                                "BORROWER": transaction_borrower,
                                "AMOUNT": amount,
                                "INSTALLMENT": installment_selection,
                                "REMARKS": remarks
                            }
                        else:
                            new_row = {
                                "DATE": date_of_transaction,
                                "DESCRIPTION": description,
                                "BANK": bank_selection.upper(),
                                "BORROWER": transaction_borrower,
                                "AMOUNT": amount,
                                "INSTALLMENT": installment_selection,
                                "REMARKS": remarks
                            }
                        # with st.spinner("Submitting...", show_time=False):
                        time.sleep(3)
                    success = st.success('Transaction submitted!', icon="✅")
                    new_row
                    time.sleep(1.5)
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
