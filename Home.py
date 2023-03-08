import streamlit as st
import hashlib
import data
import json
from pathlib import Path
from streamlit.source_util import _on_pages_changed, get_pages

DEFAULT_PAGE = "Home.py"

def register_user(email, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    sheet_url = st.secrets["user_gsheets_url"]
    
    check_query = f'select Email from "{sheet_url}" where Email = "{email}"'
    user = data.get_data(check_query)
    header = user[0]
    
    for row in user[1:]:
        if row[header.index('Email')] == email:
            return False
        else:
            insert_query = f'insert into "{sheet_url}" values("{email}", "{password}", "{0}")'
            data.write_data(insert_query)
            return True

def login_user(email, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    sheet_url = st.secrets["user_gsheets_url"]
    check_query = f'select Email, Password, Approved from "{sheet_url}" where Email = "{email}" and Password = "{hashed_password}" and Approved = "{1}"'
    
    user = data.get_data(check_query)
    header = user[0]

    for row in user[1:]:
        if row[header.index('Email')] == email and row[header.index('Password')] == hashed_password and row[header.index('Approved')] == '1':
            return True
    return False

def get_all_pages():
    default_pages = get_pages(DEFAULT_PAGE)

    pages_path = Path("pages.json")

    if pages_path.exists():
        saved_default_pages = json.loads(pages_path.read_text())
    else:
        saved_default_pages = default_pages.copy()
        pages_path.write_text(json.dumps(default_pages, indent=4))

    return saved_default_pages

def clear_all_but_first_page():
    current_pages = get_pages(DEFAULT_PAGE)

    if len(current_pages.keys()) == 1:
        return

    get_all_pages()

    # Remove all but the first page
    key, val = list(current_pages.items())[0]
    current_pages.clear()
    current_pages[key] = val

    _on_pages_changed.send()


def show_all_pages():
    current_pages = get_pages(DEFAULT_PAGE)

    saved_pages = get_all_pages()

    missing_keys = set(saved_pages.keys()) - set(current_pages.keys())

    # Replace all the missing pages
    for key in missing_keys:
        current_pages[key] = saved_pages[key]

    _on_pages_changed.send()
    
    
clear_all_but_first_page()

login_placeholder = st.empty()

with login_placeholder.container():
    st.write("""# User Login""")
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')
    b1, b2 = st.columns(2)
    submit_button = b1.button('Login')
    register_button = b2.button('Register')

if submit_button:
    if email != '' and password != '':
        if login_user(email, password):
            st.success('Logged in successfully')
            show_all_pages()
            st.write('''
                Welcome, 
                this is a prototype tools designed as Inventory Management, while providing analysis for the user.
                Changelog:
                1. Add Secure Login 
                    
                Plan:
                1. Navigation for each pages
            ''')
            login_placeholder.empty()
        else:
            clear_all_but_first_page()
            st.error('Invalid username or password')
    else:
        clear_all_but_first_page()
        st.error('Invalid username or password')
                

if register_button:
    if email != '' and password != '':
        if register_user(email, password):
            st.success('Registered successfully! You can now log in.')
        else:
            st.warning('Email already exist')
    else:
        st.error('Invalid username or password')