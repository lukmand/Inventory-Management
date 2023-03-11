import streamlit as st
import hashlib
import data
from st_aggrid import AgGrid

def get_product():
    product_url = st.secrets["product_gsheets_url"]
    product_query = f'select * from "{product_url}"'
    return data.get_data(product_query)
   
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
        if submit_form:
            st.success("New Product is added")
            get_id = max_id + 1
            data.gspread_write_data(gsheet_product, [get_id, product_name])
            if ball_check:
                data.gspread_write_data(gsheet_size, [get_id, product_name, 1, "BALL"])
            if halfball_check:
                data.gspread_write_data(gsheet_size, [get_id, product_name, 2, "1/2 BALL"])
            if pack_check:
                data.gspread_write_data(gsheet_size, [get_id, product_name, 3, "PACK BALL"])
            if roll_check:
                data.gspread_write_data(gsheet_size, [get_id, product_name, 4, "ROLL BALL"])
            st.experimental_rerun()
        

st.set_page_config(page_title='Product List - Inventory Management Tool', page_icon=':bar_chart:', layout='wide')

st.title('Product List')
st.write("Add New Product")


product_data = get_product()
#print(product_data)
#print(product_data["Product ID"].max())

add1, add2 = st.columns(2)

st.markdown('''---''')
    
with add2.container():
    grid_return = AgGrid(product_data, editable=True, fit_columns_on_grid_load=True)
    save_button = st.button("Save Data")
     
    if save_button:
        new_df = grid_return['data']
        print(new_df)
        data.gspread_upload_data("Product", new_df)
        st.success("Data is updated")    
        #st.experimental_rerun()
        
with add1.container():
    add_product(int(product_data["Product ID"].max()))
 

