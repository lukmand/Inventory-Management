import streamlit as st
import hashlib
import data
from st_aggrid import AgGrid

def get_product(secret):
    product_url = secret
    product_query = f'select * from "{product_url}"'
    return data.get_data(product_query)
    
def get_conversion(secret, id):
    url = secret
    query = f'select x."Product ID", x."Product Name", x."Unit ID" as "Original Unit ID", x."Unit Size" as "Original Unit Size", "" as "Original Quantity", y."Unit ID" as "Convert Unit ID", y."Unit Size" as "Convert Unit Size", "" as "Convert Quality" from "{secret}" as x, "{secret}" as y where x."Product ID" = "{id}" and x."Product ID" = y."Product ID" and x."Unit ID" < y."Unit ID"'
    return data.get_data(query)
   
def add_product(max_id):
    with st.form("Add Product", clear_on_submit=True):
        product_name = st.text_input("Input Product Name")
        c1, c2 = st.columns(2)

        ball_check = c1.checkbox("BALL")
        halfball_check = c1.checkbox("1/2 BALL")
        pack_check = c2.checkbox("PACK")
        roll_check = c2.checkbox("ROLL")
            
        submit_form = st.form_submit_button("Submit")
            
        gsheet_product = 'Product'
        gsheet_size = 'Unit Size'
        gsheet_convert = "Size Conversion"
        gsheet_inventory = "Inventory"
        
        inv_query = f'select max([Inventory ID]) from "{st.secrets["inventory_gsheets_url"]}"'
        inv_id = data.get_data(inv_query).iat[0, 0]
        if submit_form:
            
            get_id = max_id + 1
            data.gspread_write_data(gsheet_product, [get_id, product_name])
            if ball_check:
                data.gspread_write_data(gsheet_size, [get_id, product_name, 1, "BALL"])
                data.gspread_write_data(gsheet_inventory, [inv_id + 1, get_id, product_name, 1, "BALL", 0])
            if halfball_check:
                data.gspread_write_data(gsheet_size, [get_id, product_name, 2, "1/2 BALL"])
                data.gspread_write_data(gsheet_inventory, [inv_id + 1, get_id, product_name, 2, "1/2 BALL", 0])
            if pack_check:
                data.gspread_write_data(gsheet_size, [get_id, product_name, 3, "PACK BALL"])
                data.gspread_write_data(gsheet_inventory, [inv_id + 1, get_id, product_name, 3, "PACK BALL", 0])
            if roll_check:
                data.gspread_write_data(gsheet_size, [get_id, product_name, 3, "ROLL BALL"])
                data.gspread_write_data(gsheet_inventory, [inv_id + 1, get_id, product_name, 3, "ROLL BALL", 0])
                
            product_convert = get_conversion(st.secrets["unit_gsheets_url"], get_id) 
            #print(product_convert)
            for i in product_convert.values.tolist():
                data.gspread_write_data(gsheet_convert, i)
            st.success("New Product is added")  
            st.experimental_rerun()
            
        

st.set_page_config(page_title='Inventory Management Tool', page_icon=':bar_chart:', layout='wide')

st.title('Product List')
st.write("Add New Product")


product_data = get_product(st.secrets["product_gsheets_url"])
#print(product_data)
#print(product_data["Product ID"].max())

add1, add2 = st.columns(2)

with add2.container():
    product_grid = AgGrid(product_data, editable=True, fit_columns_on_grid_load=True)
    save_button = st.button("Save Product Data")
     
    if save_button:
        product_df = product_grid['data']
        #print(new_df)
        data.gspread_upload_data("Product", product_df)
        st.success("Data is updated")    
        #st.experimental_rerun()
        
with add1.container():
    add_product(int(product_data["Product ID"].max()))
 

st.markdown('''---''')

st.write("# Product Size List")
unit_data = get_product(st.secrets["unit_gsheets_url"])
product_unit_grid = AgGrid(unit_data, editable=True, fit_columns_on_grid_load=True)
save_unit_button = st.button("Save Unit Data")
if save_unit_button:
    unit_df = product_unit_grid['data']
    data.gspread_upload_data("Unit Size", unit_df)
    st.success("Data is updated")
    
st.markdown('''---''')

st.write("# Product Conversion List")
conversion_data = get_product(st.secrets["convert_gsheets_url"])
convert_grid = AgGrid(conversion_data, editable=True, fit_columns_on_grid_load=True)
save_convert_button = st.button("Save Conversion Data")
if save_convert_button:
    convert_df = convert_grid['data']
    data.gspread_upload_data("Size Conversion", convert_df)
    st.success("Data is updated")