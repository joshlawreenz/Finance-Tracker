import streamlit as st
from datetime import datetime
import st_yled
import plotly.express as px
import plotly.graph_objects as go

from Utilities.gsheet_functionv2 import *
from Utilities.dframe_utility import *

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
    page_title="Personal Finance Tracker",
    page_icon=PESO_ICON,
    layout="wide",
    initial_sidebar_state="auto" #"collapsed" later
)
st.title("💳 Credit Card Spending Tracker")
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
bank_list_colored = [':violet[EASTWEST]',':yellow[RCBC]',':red[BPI]']

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
# BANK Tabs
index = 0

for tab in tab_list:
    with tab:
        bank = bank_list[index]
        breakdown = get_total_amount_spent(df_display,borrowers,bank)
        bank_df = df_display[df_display["BANK"] == bank]
        
        col1,col2,col3 = st.columns([0.3,0.3,0.3],vertical_alignment="center")
        with col3:
            st.subheader("Breakdown")
            st.dataframe(breakdown,width=380,hide_index=True)
        with col1:
            display_logo(bank)
        # with col2:
        #     # df = px.data.tips()
        #     # fig = px.pie(breakdown, values='Total', names='Name',color_discrete_sequence=px.colors.sequential.RdBu)
        #     # test = st.plotly_chart(fig,on_select="rerun",key=bank)
        #     name_list = [i["Name"] for i in breakdown]
        #     value_list = [i["Total"] for i in breakdown]
        #     colors = ["purple", "green", "gold", "lightgreen"]

        #     fig = go.Figure(
        #         data=[
        #             go.Pie(
        #                 labels=name_list, 
        #                 values=value_list, 
        #                 marker=dict(colors=colors, pattern=dict(shape=[".", "x", "+", "-"])),
        #                 hole=.3)
        #             ]
        #             # ,layout_showlegend=False
        #             )
        #     fig.update_traces(hoverinfo='label+value',textinfo='label', textfont_size=20)
        #     test = st.plotly_chart(fig,on_select="rerun",key=bank)
        st.subheader("Transactions")
        st.dataframe(bank_df, width="stretch", hide_index=True)

        index += 1

filter_borrowers = []
for borrower in borrowers:
    filter_borrowers.append(borrower.capitalize())

default_borrowers = [i.capitalize() for i in default_borrowers]

col1, col2, col3 = st.columns([0.75,0.45,0.10],vertical_alignment="bottom")
with col2:
    filter_options = st.multiselect(
        "Filter",
        default_borrowers,
        default= default_borrowers,
        # on_change=apply_button(),
        label_visibility = 'collapsed'
    )
    st.session_state['filter_name'] = filter_options
with col3:
    # apply_button = st_yled.button('Apply',type='secondary')
    apply_button = st_yled.button('Apply', type="secondary",font_size="13.0px",
                                #   background_color="#2E2E2E",color="#FFD700"
                                  )
    if apply_button:
        st.rerun()


### SIDEBAR FOOTER
with st.sidebar:
    st.title("Top Spenders for this Month 💵")
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
            st.markdown(f"## <span style='color: #AFED32'>{spender["Total"]}</span>", 
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
        st.space(size="large")
        space +=1
    st.space(size="small")
    st.divider()
    st.write("This is my personal spending tracker which is currently synced to my Google Sheets account.")
    st.write("This is still a work in progress.")
    st.write("## Josh V. " + "૮ ･ ﻌ･ა")
    st.divider()
    st.caption(f"{datetime.now().strftime("%A | %B %d, %Y")}")

# df = st.dataframe(df, width="stretch", hide_index=True)
# st_yled.table(df, background_color="#041d36", color="#d5d9dd",border_style="solid")
