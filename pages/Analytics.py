import streamlit as st
import hashlib
import data
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

invoice_url = st.secrets["invoice_gsheets_url"]
inventory_url = st.secrets["inventory_gsheets_url"]
size_url = st.secrets["unit_gsheets_url"]
conversion_url = st.secrets["convert_gsheets_url"]
transaction_url = st.secrets["transaction_gsheets_url"]
gsheet_transaction = "Transaction"
gsheet_invoice = "Invoice"
gsheet_inventory = "Inventory"

st.set_page_config(page_title='Inventory Management Tool', page_icon=':bar_chart:', layout='wide')
    
def approach_maturity_analytics(invoice_url):
    client = data.init_gsheet()
    cursor = client.cursor()
    
    query = '''
        select
            *,
            case when [Maturity Date] is null then cast(julianday(date()) - julianday(Date) as int)
                 else cast(julianday([Maturity Date]) - julianday(Date) as int)
            end Remaining_Days
        from "{invoice_url}"
        where Status = "INVOICE"
    '''.format(invoice_url = invoice_url)
    
    inv_res = cursor.execute(query).fetchall()
    inv_df = pd.DataFrame.from_records(inv_res, columns = [column[0] for column in cursor.description])
    
    return inv_df

st.write('''
	# Inventory & Invoice Analytics
''')

st.markdown(''' --- ''')

st.write("Approaching MaturityDate")
inv_df = approach_maturity_analytics(invoice_url).sort_values('Remaining_Days')
AgGrid(inv_df, fit_columns_on_grid_load=True)

