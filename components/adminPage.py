import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import date, timedelta

from components.firebase import get_credentials, get_users, update_value

from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials
try:
    app = firebase_admin.get_app("firebase_connector")
except ValueError:
    cred = credentials.Certificate('./configuration/m8-agency-2e7b37294714.json')
    app = firebase_admin.initialize_app(cred, name="firebase_connector")

db = firestore.client(app)

transaction_type = {
    "Добавить": "bonus charge",
    "Вычесть": "bonus write off",
    "Зарезирвировать": "bonus reserve"
}

user_map = dict()

def update_user_bonus_table():
    st.session_state.bonus_delta = st.session_state.new_bonus_delta_widget
    st.session_state.new_bonus_delta_widget = 0

def update_table_create_new_reward():
    st.session_state.reward_disc = st.session_state.reward_disc_widget
    st.session_state.reward_price = st.session_state.reward_price_widget

    st.session_state.reward_disc_widget = None
    st.session_state.reward_price_widget = None


def update_table_update_reward():
    st.session_state.reward_disc = st.session_state.edit_reward_disc_widget
    st.session_state.reward_price = st.session_state.edit_reward_price_widget

    st.session_state.edit_reward_disc_widget = None
    st.session_state.edit_reward_price_widget = None


def update_table_create_new_challenge():
    st.session_state.task_description = st.session_state.task_disc_widget
    st.session_state.task_award = st.session_state.task_award_widget
    st.session_state.task_planned_time = st.session_state.task_planned_time_widget

    # clean text fields
    st.session_state.task_disc_widget = None
    st.session_state.task_award_widget = None
    st.session_state.task_planned_time_widget = None


def update_table_update_challenge():
    st.session_state.task_description = st.session_state.edit_challenge_disc_widget
    st.session_state.task_award = st.session_state.edit_challenge_reward_widget
    st.session_state.task_planned_time = st.session_state.edit_challenge_planned_time_widget

    # clean text fields
    st.session_state.edit_challenge_disc_widget = None
    st.session_state.edit_challenge_reward_widget = None
    st.session_state.edit_challenge_planned_time_widget = None

def show_admin_page():
    # initialize session variables
    if "task_description" not in st.session_state:
        st.session_state.task_description = ""
        st.session_state.task_award = ""
        st.session_state.task_planned_time = ""
    if "reward_disc" not in st.session_state:
        st.session_state.reward_disc = ""
        st.session_state.reward_price = ""
    if "bonus_delta" not in st.session_state:
        st.session_state.bonus_delta = None


    with st.sidebar:
        selected = option_menu("M8.Agenсy", ["Сотрудники", "Задания", "Награды", "Аналитика"],
                               icons=['house', "list-task", "award"], menu_icon="cast", default_index=0)
    # initialization of dataframes

    fire_users = get_users()
    for key, value in fire_users.items():
        user_map[value["user_name"]] = key
    users_list = list(user_map.keys())

    if selected == "Сотрудники":
        st.subheader("Сотрудники")
        selected_user = st.selectbox(label="Cотрудник", index=None, placeholder='Выберите сотрудника',
                                     options=users_list)
        if selected_user:
            user_name = user_map[selected_user]
            st.write()
            user_account = int(fire_users[user_name]["user_free_bonuses"])
            tab1, tab2 = st.tabs(["📈 Управление бонусами", "🗃 Управление задачами"])
            additional_bonus = 0
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    additional_bonus = st.number_input(label="Бонусы", value=0, placeholder="Введите количество бонусов",
                                                       key="new_bonus_delta_widget")
                    operation = st.radio(label="Операция", options=["Добавить", "Вычесть"], horizontal=True)
                    if operation == "Вычесть":
                        additional_bonus *= (-1)
                    add_bonus = st.button("Изменить баланс", on_click=update_user_bonus_table)
                with col2:
                    st.metric(label="Текущий баланс", value=user_account, delta=additional_bonus,
                              delta_color="normal", help=None, label_visibility="visible")
                if add_bonus:
                    new_balance = user_account + int(st.session_state.bonus_delta if operation == "Добавить"
                                                     else st.session_state.bonus_delta * (-1))
                    if update_value(collection="users", document=user_name,
                                    field="user_free_bonuses", value = new_balance):
                        st.cache_data.clear()
                        st.rerun()