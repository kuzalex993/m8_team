# utils.py
import streamlit as st

def authenticate(username, password, user_data):
    if username in user_data and user_data[username]["password"] == password:
        return user_data[username]["role"]
    return None
