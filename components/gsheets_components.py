from streamlit_gsheets import GSheetsConnection
from datetime import date
import streamlit as st
import pandas as pd

conn = st.connection("gsheets", type=GSheetsConnection)


def add_new_record(table_name: str, values_to_add: dict):
    data_from_gsh = conn.read(worksheet=table_name)
    data_from_gsh = data_from_gsh.dropna(subset=["user_challenge_id"])
    new_row = pd.DataFrame([values_to_add])
    data_from_gsh = pd.concat([data_from_gsh, new_row], ignore_index=True)
    response = conn.update(worksheet=table_name, data=data_from_gsh)
    st.cache_data.clear()
    st.rerun()
    print(response)
