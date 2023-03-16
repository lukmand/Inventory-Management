import streamlit as st
import hashlib
import data
import pandas as pd
from st_aggrid import AgGrid
import datetime


product_dict = {}
size_dict = {}
inventory_url = st.secrets["inventory_gsheets_url"]
size_url = st.secrets["unit_gsheets_url"]
conversion_url = st.secrets["convert_gsheets_url"]
transaction_url = st.secrets["transaction_gsheets_url"]
gsheet_transaction = "Transaction"
gsheet_invoice = "Invoice"
gsheet_inventory = "Inventory"

if "transaction_df" not in st.session_state:
    st.session_state.transaction_df = pd.DataFrame(columns = ["Transaction ID", "Invoice ID", "Product ID", "Product Name", "Transaction", "Quantity", "Unit ID", "Unit Size", "Price", "Disc1", "Disc2", "Disc3", "Total Prize"])

def get_product(secret):
    product_url = secret
    product_query = f'select * from "{product_url}"'
    return data.get_data(product_query)

def format_func(option):
    return product_dict[option]

def format_func2(option):
    return size_dict[option]
    
def get_stock(inventory_url, conversion_url, product_size, option):
    val_query = f'select sum((x.Stock/ifnull(y.[Original Quantity], 1)) * ifnull(y.[Convert Quantity], 1)) from "{inventory_url}" x left join "{conversion_url}" y on x.[Product ID] = y.[Product ID] and x.[Unit ID] = y.[Original Unit ID] and y.[Convert Unit ID] = "{product_size}" where x.[Product ID] = "{option}" and x.[Unit ID] <= "{product_size}"'
    #print(val_query)
    val_df = data.get_data(val_query)
    #print(val_df)
    maxvalue = val_df.iat[0, 0]
    #print(maxvalue)
    return maxvalue
    
def get_stock_list(option, inventory_url):
    stock_query = f'select Stock, [Unit Size] from "{inventory_url}" where [Product ID] = "{option}"'
    return data.get_data(stock_query)
    
def get_size_list(option, size_url):
    size_dict = {}
    size_query = f'select [Unit ID], [Unit Size] from "{size_url}" where [Product ID] = "{option}"'
    size_df = data.get_data(size_query)

    for j in size_df.values.tolist():
        size_dict[j[0]] = j[1]
        
    return size_dict
    
def get_discount(product_quantity, product_size, product_in):
    disc1 = 0.00
    disc2 = 0.00
    disc3 = 0.00
    if product_size == 1 and product_in == "OUT":
        if product_quantity >= 5 and product_quantity < 30:
            disc1 = .02
        elif product_quantity >= 30 and product_quantity < 60:
            disc1 = .02
            disc2 = .01
        elif product_quantity >= 60 and product_quantity < 100:
            disc1 = .02
            disc2 = .02  
        elif product_quantity >= 100:
            disc1 = .02
            disc2 = .03
        else:
            pass
    return disc1, disc2, disc3

st.write('''
    # Add Transaction
''')

c1, c2 = st.columns(2, gap="small")
product_df = get_product(st.secrets["product_gsheets_url"])
for i in product_df.values.tolist():
    product_dict[i[0]] = i[1]
#print(product_dict)

c1.write("Find your Product Here")
option = c1.selectbox("Select Product", options = list(product_dict.keys()), format_func = format_func)

with c1.container():
    st.write("Current Stock:")
    AgGrid(get_stock_list(option, inventory_url), editable=False, fit_columns_on_grid_load=True)

c3, c4, c5 = c1.columns(3)
product_in = c3.radio("Select Transaction", ("IN", "OUT"))

size_dict = get_size_list(option, size_url)
product_size = c5.selectbox("Select Unit", options = list(size_dict.keys()), format_func = format_func2)

#maxvalue = get_stock(inventory_url, conversion_url, product_size, option)
product_quantity = c4.number_input("Enter Quantity", min_value=0)
product_prize = c1.number_input("Enter Prize per Unit", min_value = 0)

add_transaction = c1.button("Add Transaction")

if add_transaction:

    disc1, disc2, disc3 = get_discount(product_quantity, product_size, product_in)
    total_prize = product_quantity * product_prize
    disc1_prize = disc1 * total_prize
    disc2_prize = disc2 * (total_prize - disc1_prize)
    disc3_prize = disc3 * (total_prize - disc1_prize - disc2_prize)
    final_prize = total_prize - disc1_prize - disc2_prize - disc3_prize
    st.session_state.transaction_df.loc[len(st.session_state.transaction_df)] = [str(option)+"_"+str(datetime.datetime.now().timestamp()), "", option, format_func(option), product_in, product_quantity, product_size, format_func2(product_size), product_prize, str(disc1*100) + '%', str(disc2*100) + '%', str(disc3*100) + '%', final_prize]

    
st.markdown(''' --- ''')

st.write("# Transaction List")
with st.container():
    vendor = st.text_input("Enter Vendor/Sales Name")
    AgGrid(st.session_state.transaction_df, editable=False, fit_columns_on_grid_load=True)

c6, c7 = st.columns(2)
submit = c6.button("Submit Invoice")
clear = c7.button("Clear")

if submit:
    if vendor == "":
        st.error("Vendor Name is Empty")
    else:
        #if readjust_stock(st.session_state.transaction_df, inventory_url, conversion_url):
        #calculate_in(st.session_state.transaction_df)
        #calculate_out(st.session_state.transaction_df)
        invoiceid = "INV_"+str(datetime.datetime.now().timestamp())
        invoiceprize = st.session_state.transaction_df["Total Prize"].sum()
            
        st.session_state.transaction_df["Invoice ID"] = invoiceid
        for i in st.session_state.transaction_df.values.tolist():
            data.gspread_write_data(gsheet_transaction, i)
        
        data.gspread_write_data(gsheet_invoice, [invoiceid, str(datetime.datetime.now().isoformat()), "PROCESS", vendor, invoiceprize, 0])
        st.session_state.transaction_df = st.session_state.transaction_df.iloc[0:0]
        st.experimental_rerun()
        #else:
        #    st.warning("item exceeds stocks")
        
        
        
if clear:
    st.session_state.transaction_df = st.session_state.transaction_df.iloc[0:0]


st.markdown(''' --- ''')

st.write("# Transaction History List")
transaction_history = get_product(transaction_url)
AgGrid(transaction_history, editable=False, fit_columns_on_grid_load=True, key = 'transaction_history')
