

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
    # if isinstance(borrower,list):
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