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

def get_product(secret):
    product_url = secret
    product_query = f'select * from "{product_url}"'
    return data.get_data(product_query)
    
def get_invoice_detail(df, transaction_url):
    query = '''
        select
            y.*
        from df x
        inner join "{transaction_url}" y on x.[Invoice ID] = y.[Invoice ID]
    '''.format(transaction_url = transaction_url)
    
    
    return data.get_data(query)
    
def edit_invoice(df, gsheet_invoice):
    client = data.init_gsheet()
    cursor = client.cursor()
    
    edit_query = '''
        update df
        set isProcess = 1
        where Status = 'INVOICE'
    '''
    cursor.execute(edit_query)
    #print(df)
    data.gspread_upload_data(gsheet_invoice, df)
    

def calculate_in(df, transaction_url, inventory_url, gsheet_inventory):
    inventory_data = get_product(inventory_url)
    client = data.init_gsheet()
    cursor = client.cursor()
    
    update_query = '''
        update inventory_data
        set Stock = inventory_data.Stock + x.Stock
        from (
            select y.[Product ID], y.[Unit ID], sum(y.Quantity) Stock
            from df x
            inner join "{transaction_url}" y on x.[Invoice ID] = y.[Invoice ID]
            where y.[Transaction] = "IN"
                and x.[Status] = "INVOICE"
                and x.[isProcess] = 0
            group by y.[Product ID], y.[Unit ID]
        ) x
        where x.[Product ID] = inventory_data.[Product ID]
            and x.[Unit ID] = inventory_data.[Unit ID]
    '''.format(transaction_url=transaction_url)
    cursor.execute(update_query)
    data.gspread_upload_data(gsheet_inventory, inventory_data)
    
def calculate_out(df, inventory_url, conversion_url, transaction_url, inventory_gsheets_url):
    inventory_data = get_product(inventory_url)
    client = data.init_gsheet()
    cursor = client.cursor()
    
    conversion_data = get_product(conversion_url)
    out_query = '''
        select y.[Product ID], y.[Unit ID], sum(y.Quantity) Stock
        from df x
        inner join "{transaction_url}" y on x.[Invoice ID] = y.[Invoice ID]
        where y.[Transaction] = "OUT"
            and x.[Status] = "INVOICE"
            and x.[isProcess] = 0
        group by y.[Product ID], y.[Unit ID]
    '''.format(transaction_url = transaction_url)
    
    out_res = cursor.execute(out_query).fetchall()
    out_df = pd.DataFrame.from_records(out_res, columns = [column[0] for column in cursor.description])
    
    #print(out_df)
    sum_query = '''
        select 
            x.*,
            case when y.Stock is null then 0            
                 else y.Stock 
            end as Buy,
            cast(null as int) [Original ID],
            cast(null as int) [Convert Qty],
            cast(null as int) [Multiplier],
            cast(null as int) [Remaining]
        from inventory_data x
        left join out_df y on x.[Product ID] = y.[Product ID] and x.[Unit ID] = y.[Unit ID]
    '''
    sum_res = cursor.execute(sum_query).fetchall()
    
    sum_df = pd.DataFrame.from_records(sum_res, columns = [column[0] for column in cursor.description])
    
    convert_pack_query = '''
        update sum_df
        set [Original ID] = x.[Original Unit ID],
            [Convert Qty] = x.[Convert Quantity],
            [Multiplier] = ceil((cast((Buy - Stock) as float)/x.[Convert Quantity]))
        from conversion_data x
        where x.[Product ID] = sum_df.[Product ID]
            and sum_df.Buy is not null
            and sum_df.Buy > sum_df.Stock
            and sum_df.[Unit ID] = 3
            and x.[Convert Unit ID] = sum_df.[Unit ID]
            and x.[Original Unit ID] = sum_df.[Unit ID] - 1 
    '''
    
    update_pack_query = '''
        update sum_df
        set Stock = Stock + ([Multiplier] * [Convert Qty])
        where sum_df.Buy is not null
            and sum_df.Buy > sum_df.Stock
            and sum_df.[Unit ID] = 3
    '''
    
    normalize_pack = '''
        update sum_df
        set Buy = Buy + x.Multiplier
        from (
            select [Product ID], [Original ID], [Multiplier] 
            from sum_df
            where cast([Original ID] as int) = 2
        ) x
        where x.[Product ID] = sum_df.[Product ID]
            and x.[Original ID] = sum_df.[Unit ID]
    '''
    
    convert_halfball_query = '''
        update sum_df
        set [Original ID] = x.[Original Unit ID],
            [Convert Qty] = x.[Convert Quantity],
            [Multiplier] = ceil((cast((Buy - Stock) as float)/x.[Convert Quantity]))
        from conversion_data x
        where x.[Product ID] = sum_df.[Product ID]
            and sum_df.Buy is not null
            and sum_df.Buy > sum_df.Stock
            and sum_df.[Unit ID] = 2
            and x.[Convert Unit ID] = sum_df.[Unit ID]
            and x.[Original Unit ID] = sum_df.[Unit ID] - 1 
    '''
    
    update_halfball_query = '''
        update sum_df
        set Stock = Stock + ([Multiplier] * [Convert Qty])
        where sum_df.Buy is not null
            and sum_df.Buy > sum_df.Stock
            and sum_df.[Unit ID] = 2
    '''
    
    normalize_halfball = '''
        update sum_df
        set Buy = Buy + x.Multiplier
        from (
            select [Product ID], [Original ID], [Multiplier] 
            from sum_df
            where cast([Original ID] as int) = 1
        ) x
        where x.[Product ID] = sum_df.[Product ID]
            and x.[Original ID] = sum_df.[Unit ID]
    '''
    final_query = '''
        select 
            [Inventory ID],
            [Product ID],
            [Product Name],
            [Unit ID],
            [Unit Size],
            Stock - Buy as Stock
        from sum_df
    '''
    
    cursor.execute(convert_pack_query)
    cursor.execute(update_pack_query)
    cursor.execute(normalize_pack)
    cursor.execute(convert_halfball_query)
    cursor.execute(update_halfball_query)
    cursor.execute(normalize_halfball)
    final_res = cursor.execute(final_query)
    
    final_df = pd.DataFrame.from_records(final_res, columns = [column[0] for column in cursor.description])
    
    data.gspread_upload_data(gsheet_inventory, final_df)
    
    

def readjust_stock(df, inventory_url, conversion_url, transaction_url):
    client = data.init_gsheet()

    cursor = client.cursor()
    
    inv_query = '''
        select x.[Product ID], sum((x.Stock/ifnull(y.[Original Quantity], 1)) * ifnull(y.[Convert Quantity], 1)) as [StockPack]
            from "{inventory_url}" x
            left join "{conversion_url}" y on x.[Product ID] = y.[Product ID] and x.[Unit ID] = y.[Original Unit ID] and y.[Convert Unit ID] = 3
            group by x.[Product ID]
    '''.format(inventory_url = inventory_url, conversion_url = conversion_url)
    
    trans_query = '''
        select x.[Product ID], sum((x.Stock/ifnull(y.[Original Quantity], 1)) * ifnull(y.[Convert Quantity], 1)) as [StockPack]
        from (
            select y.[Product ID], y.[Unit ID], sum(y.Quantity) Stock
            from df x
            inner join "{transaction_url}" y on x.[Invoice ID] = y.[Invoice ID]
            where y.[Transaction] = "OUT"
                and x.[Status] = "PAID"
                and x.[isProcess] = 0
            group by y.[Product ID], y.[Unit ID]
        ) x
        left join "{conversion_url}" y on x.[Product ID] = y.[Product ID] and x.[Unit ID] = y.[Original Unit ID] and y.[Convert Unit ID] = 3
        group by x.[Product ID]
    '''.format(conversion_url = conversion_url, transaction_url = transaction_url)
    
    val_query = '''
        select 
            a.[Product ID], 
            a.[StockPack], 
            b.[StockPack] as [PackBuy], 
            case when a.[StockPack] >= b.[StockPack] then True
                 else False
            end as TruthValue
        from inv a
        inner join trans b on a.[Product ID] = b.[Product ID]
    '''
    inv_results = cursor.execute(inv_query).fetchall()
    trans_results = cursor.execute(trans_query).fetchall()
    
    inv = pd.DataFrame.from_records(inv_results, columns = [column[0] for column in cursor.description])
    trans = pd.DataFrame.from_records(trans_results, columns = [column[0] for column in cursor.description])
    results = cursor.execute(val_query).fetchall()
    res = pd.DataFrame.from_records(results, columns = [column[0] for column in cursor.description])

    #print(inv)
    #print(trans)
    #print(res)
    for i in res["TruthValue"]:
        if i == False:
            return False
    return True



st.write('''
	# List of Invoice
''')

status_list = ('PROCESS', 'CANCELLED', 'INVOICE')
invoice_data = get_product(invoice_url)
gb = GridOptionsBuilder.from_dataframe(invoice_data)
gb.configure_column("Status", editable = True, cellEditor = 'agSelectCellEditor', cellEditorParams = {'values': status_list})
gb.configure_selection(use_checkbox = True)
vgo = gb.build()

invoice_grid = AgGrid(invoice_data, gridOptions = vgo, fit_columns_on_grid_load=True)

save_invoice_button = st.button("Save Invoice Data")
if save_invoice_button:
    invoice_df = invoice_grid['data']
    if readjust_stock(invoice_df, inventory_url, conversion_url, transaction_url):  
        #calculate_in(invoice_df, transaction_url, inventory_url, gsheet_inventory)
        calculate_out(invoice_df, inventory_url, conversion_url, transaction_url, gsheet_inventory)
        edit_invoice(invoice_df, gsheet_invoice)
        
        st.success("Success")
        st.experimental_rerun()
    else:
        st.error("Item Exceeds Stock")
        
st.markdown(''' --- ''')



select_invoice = invoice_grid['selected_rows']
if select_invoice:
    st.write("# Invoice Detail")
    AgGrid(get_invoice_detail(pd.DataFrame(select_invoice), transaction_url), fit_columns_on_grid_load=True)
    
    print_bill = st.button("Print Invoice")
