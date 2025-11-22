from datetime import datetime
import calendar

now = datetime.now()

#Get Borrowers list
def get_borrowers_list(dataframe):

    borrowers = []
    
    for borrower in dataframe["BORROWER"]:
        try:
            split_borrower = borrower.split(", ")
            for i in split_borrower:
                borrowers.append(i.strip())
        except:
            borrowers.append(borrower)

    borrowers_list = list(set(borrowers))

    return borrowers_list

def get_bank_list(dataframe):
    banks = []

    for bank in dataframe["BANK"]:
        banks.append(bank.strip())

    bank_list = list(set(banks))

    return bank_list

def get_total_amount_spent(dataframe,borrowers,bank=None):
    total_amount = []
    for borrower in borrowers:
        borrower_df = dataframe[dataframe["BORROWER"]==borrower.upper()]

        if bank:
            borrower_df = borrower_df[borrower_df["BANK"] == bank]

        total = 0
        for amount in borrower_df["AMOUNT"]:
            total += float(amount.replace(",",""))

        borrower_json = {
            "Name": borrower.capitalize(),
            "Total": total
        }
        total_amount.append(borrower_json)
    total_amount = sorted(total_amount, key=lambda x: x['Total'], reverse=True)
    return total_amount

def get_monthly_due(dataframe,bank):
    if bank:
        dataframe = dataframe[dataframe["BANK"] == bank]

    total = 0
    for amount in dataframe["AMOUNT"]:
        total += float(amount.replace(",",""))

    return total


# Create JSON for bank details
def generate_bank_details(bank_list):
    bank_details_list = []
    for bank in bank_list:
        if now.day in range(1,3):
            month_int = now.month
        else:
            month_int = now.month + 1

        if month_int > 12:
            month_int -= 12

        due_month = calendar.month_name[month_int].capitalize()
        total_amount_string = f"Total Amount :color[(Due date: {due_month} 28])"

        if bank == 'EASTWEST':
            total_amount_string = total_amount_string.replace(':color',":violet")
        elif bank == 'RCBC':
            total_amount_string = total_amount_string.replace(':color',":blue")
        elif bank == 'BPI':
            if now.day in range(1,15):
                month_int = now.month
            else:
                month_int = now.month + 1

            if month_int > 12:
                month_int -= 12

            due_month = calendar.month_name[month_int].capitalize()
            total_amount_string = f"Total Amount :red[(Due date: {due_month.capitalize()} 03])"

        bank_details = {
            "bank": bank,
            "total_amount_string": total_amount_string
        }
        bank_details_list.append(bank_details)

    return bank_details_list