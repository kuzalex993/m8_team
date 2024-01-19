import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(page_title="User Page", page_icon="📈")

# 1. as sidebar menu
with st.sidebar:
    selected = option_menu("M8Agensy", ["Главная", "Мои задачи", "Награды", "Доска"],
                           icons=['house', "list-task", "award", "bi-bar-chart"], menu_icon="cast", default_index=0)
if selected=="Главная":
    st.write("Здесь мы разместим персональный дашбрд")
    st.metric(label="Бонусы", value="70", delta="10")
elif selected=="Мои задачи":
    st.write("Здесь мы разместим список задач, по которым можно будет вести статус")
elif selected=="Награды":
    st.write("Здесь мы разместим список наград, на которые можно будет потратить свои бонусы")
elif selected=="Доска":
    st.write("Здесь мы разместим общекомандные результаты")