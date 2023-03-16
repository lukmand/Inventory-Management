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
purchase_url = st.secrets["purchase_gsheets_url"]
gsheet_purchase = "Purchase"
gsheet_invoice = "Invoice"
gsheet_inventory = "Inventory"

def get_product(secret):
    product_url = secret
    product_query = f'select * from "{product_url}"'
    return data.get_data(product_query)

def format_func(option):
    return product_dict[option]

def format_func2(option):
    return size_dict[option]
    
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
    
def calculate_in(option, product_size, product_quantity, inventory_url, gsheet_inventory):
    inventory_data = get_product(inventory_url)
    client = data.init_gsheet()
    cursor = client.cursor()
    
    update_query = '''
        update inventory_data
        set Stock = inventory_data.Stock + Quantity
        where inventory_data.[Product ID] = {option}
            and inventory_data.[Unit ID] = {product_size}
    '''.format(option=option, product_size = product_size)
    cursor.execute(update_query)
    data.gspread_upload_data(gsheet_inventory, inventory_data)

st.write('''
	# Purchase order
''')

c1, c2 = st.columns(2)
product_df = get_product(st.secrets["product_gsheets_url"])
for i in product_df.values.tolist():
    product_dict[i[0]] = i[1]
#print(product_dict)

c1.write("Find your Product Here")
option = c1.selectbox("Select Product", options = list(product_dict.keys()), format_func = format_func)

with c1.container():
    st.write("Current Stock:")
    AgGrid(get_stock_list(option, inventory_url), editable=False, fit_columns_on_grid_load=True)

c4, c5 = c1.columns(2)
#product_in = c3.radio("Select Transaction", ("IN", "OUT"))
product_in = "IN"

size_dict = get_size_list(option, size_url)
product_size = c5.selectbox("Select Unit", options = list(size_dict.keys()), format_func = format_func2)

#maxvalue = get_stock(inventory_url, conversion_url, product_size, option)
product_quantity = c4.number_input("Enter Quantity", min_value=0)
product_price = c1.number_input("Enter Total Price", min_value = 0)

add_transaction = c1.button("Add Purchase")

if add_transaction:
    calculate_in(option, product_size, product_quantity, inventory_url, gsheet_inventory)
    data.gspread_write_data(gsheet_purchase, [product_in+_+str(option)+"_"+str(datetime.datetime.now().timestamp()), option, format_func(option), product_in, product_quantity, product_size, format_func2(product_size), ])
    st.success("Purchase Added")
    st.experimental_rerun()
    
st.markdown('''---''')

st.write("# Purchase History List")
purchase_history = get_product(purchase_url)
AgGrid(purchase_history, editable=False, fit_columns_on_grid_load=True, key = 'purchase_history')

