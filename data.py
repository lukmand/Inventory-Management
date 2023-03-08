import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def init_gspread():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    # specify the path to the API credentials file
    creds = ServiceAccountCredentials.from_json_keyfile_name('project-streamlit-379903-0600fa4a998c.json', scope)

    # authorize the API client
    client = gspread.authorize(creds)
    return client

# define the scope of the API credentials
def get_data(sheet_name):
    client = init_gspread()

    # open the specified spreadsheet
    sheet = client.open('Streamlit').worksheet(sheet_name)

    # read the data from the sheet
    data = sheet.get_all_values()

    # print the data
    return data
    
def write_data(data, sheet_name):
    client = init_gspread()
    
    # open the specified spreadsheet
    sheet = client.open('Streamlit').worksheet(sheet_name)
    
    sheet.append_row(data)
 