import streamlit as st
import pandas as pd
from shillelagh.backends.apsw.db import connect
from google.oauth2 import service_account


def init_gsheet():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive'],
    )
    connection = connect(":memory:", adapter_kwargs={
        "gsheetaspi": {
            "service_account_info": {
                "type": st.secrets["gcp_service_account"]["type"],
                "project_id": st.secrets["gcp_service_account"]["project_id"],
                "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
                "private_key": st.secrets["gcp_service_account"]["private_key"],
                "client_email": st.secrets["gcp_service_account"]["client_email"],
                "client_id": st.secrets["gcp_service_account"]["client_id"],
                "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
                "token_uri": st.secrets["gcp_service_account"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
                }
            },
        })
        
   # authorize the API client
    return connection

# define the scope of the API credentials
def get_data(query):
    client = init_gsheet()
    
    # open the specified spreadsheet
    cursor = client.cursor()
    rows = pd.DataFrame(cursor.execute(query))

    # print the data
    return rows
    
def write_data(query):
    client = init_gsheet()
    
    # open the specified spreadsheet
    cursor = client.cursor()
    cursor.execute(query)

sheet_url = st.secrets["user_gsheets_url"]
query = f'SELECT * FROM "{sheet_url}"'
get_data(query)