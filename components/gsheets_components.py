from streamlit_gsheets import GSheetsConnection
from datetime import date
import streamlit as st
import pandas as pd

conn = st.connection("gsheets", type=GSheetsConnection)


def add_new_record(table_name: str, values_to_add: list):
    data_from_gsh = conn.read(worksheet=table_name)
    data_from_gsh = data_from_gsh.dropna(subset=[f"{table_name}_id"])
    next_id = data_from_gsh[f"{table_name}_id"].max() + 1
    for row in values_to_add:
        row[f"{table_name}_id"] = next_id
        new_row = pd.DataFrame([row])
        data_from_gsh = pd.concat([data_from_gsh, new_row], ignore_index=True)
        next_id += 1

    response = conn.update(worksheet=table_name, data=data_from_gsh)
    st.cache_data.clear()
    st.rerun()
    print(response)
