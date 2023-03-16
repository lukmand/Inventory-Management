import streamlit as st
import hashlib
import data
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

def get_product(secret):
    product_url = secret
    product_query = f'select * from "{product_url}"'
    return data.get_data(product_query)

st.write('''
	# Inventory Page
''')

inventory_data = get_product(st.secrets["inventory_gsheets_url"])
inventory_grid = AgGrid(inventory_data, editable=True, fit_columns_on_grid_load=True)
save_inventory_button = st.button("Save Inventory Data")
if save_inventory_button:
    inventory_df = inventory_grid['data']
    data.gspread_upload_data("Inventory", inventory_df)
    st.success("Data is updated")