import streamlit as st
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
from streamlit_echarts import st_echarts

from components.firebase import (get_document,put_into_user_bonus_collection, put_into_user_challenge_collection,
                                 get_users, update_value, add_new_document,
                                 get_collection, update_document)

def draw_bonus_chart(_free_bonus: int, _reserved_bonus: int) -> dict:
    options = {
        "tooltip": {"trigger": "item"},
        "legend": {"top": "5%", "left": "center"},
        "series": [
            {
                "name": "Мои бонусы",
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {"show": False, "position": "center"},
                "emphasis": {
                    "label": {"show": True, "fontSize": "36", "fontWeight": "bold"}
                },
                "labelLine": {"show": False},
                "data": [
                    {"value": _free_bonus, "name": "Доступно"},
                    {"value": _reserved_bonus, "name": "Резерв"}
                ],
            }
        ],
    }
    return options

if "free_bonus" not in st.session_state:
        st.session_state.free_bonus = None
if "reserved_bonus" not in st.session_state:
    st.session_state.reserved_bonus = None

def get_bonus(user_id: str) -> list:
    user_data = get_document(collection_name="users",document_name=user_id)
    f_bonus = user_data["user_free_bonuses"]
    r_bonus = user_data["user_reserved_bonuses"]
    return f_bonus, r_bonus

def show_user_page():

    with st.sidebar:
        selected = option_menu("M8Agensy", ["Главная", "Мои задачи", "Награды", "Доска"],
                               icons=['house', "list-task", "award", "bi-bar-chart"], menu_icon="cast", default_index=0)

    if selected=="Главная":
        with st.container():
            free_bonus, reserved_bonus = get_bonus(st.session_state.username)
            chart_options = draw_bonus_chart(_free_bonus=free_bonus, _reserved_bonus=reserved_bonus)
            st_echarts(options=chart_options, height="500px")
    elif selected=="Мои задачи":
        st.write("Здесь мы разместим список задач, по которым можно будет вести статус")
    elif selected=="Награды":
        st.write("Здесь мы разместим список наград, на которые можно будет потратить свои бонусы")
    elif selected=="Доска":
        st.write("Здесь мы разместим общекомандные результаты")