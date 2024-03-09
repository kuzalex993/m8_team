import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import date, timedelta, datetime


import logging

from components.firebase import get_credentials, get_users, update_value, get_challenges, add_new_document, update_document

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


def add_new_challenge():
    st.session_state.task_description = st.session_state.task_disc_widget
    st.session_state.task_award = st.session_state.task_award_widget
    st.session_state.task_planned_time = st.session_state.task_planned_time_widget

    new_task = {
        "challenge_description": st.session_state.task_description,
        "challenge_reward": st.session_state.task_award,
        "challenge_planned_time_completion": st.session_state.task_planned_time,
        "challenge_active": True,
        "challenge_date_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }
    if add_new_document(collection_name="challenges", document_data=new_task):
        st.session_state.transaction_status = True

    # clean text fields
    st.session_state.task_disc_widget = None
    st.session_state.task_award_widget = None
    st.session_state.task_planned_time_widget = None

    # retrieve updated data from firebase
    st.session_state.challenge_df = get_challenges_df()


def update_table_update_challenge(challenge_id):
    st.session_state.task_description = st.session_state.edit_challenge_disc_widget
    st.session_state.task_award = st.session_state.edit_challenge_reward_widget
    st.session_state.task_planned_time = st.session_state.edit_challenge_planned_time_widget
    st.session_state.challenge_id_to_edit = challenge_id

    edited_task = {
        "challenge_description": st.session_state.task_description,
        "challenge_reward": st.session_state.task_award,
        "challenge_planned_time_completion": st.session_state.task_planned_time,
        "challenge_active": True,
        "challenge_date_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }
    if update_document(collection_name="challenges",
                       document_id=st.session_state.challenge_id_to_edit,
                       document_data=edited_task):
        st.session_state.transaction_status = True


    # clean text fields
    st.session_state.challenge_to_edit = None
    st.session_state.edit_challenge_disc_widget = None
    st.session_state.edit_challenge_reward_widget = None
    st.session_state.edit_challenge_planned_time_widget = None

    # retrieve updated data from firebase
    st.session_state.challenge_df = get_challenges_df()

@st.cache_data
def get_user_bonus(selected_user_name: str) -> int:
    print("Getting user bonus")
    users_data = get_users()
    user_account = int(users_data[selected_user_name]["user_free_bonuses"])
    return user_account

@st.cache_data
def get_users_map() -> dict():
    print("Getting users list")
    cred = get_credentials()
    fire_users = cred["credentials"]["usernames"]
    for key, value in fire_users.items():
        if key != "admin":
            user_map[value["name"]] = key
    return user_map


def get_challenges_df():
    print("Getting challenges list")
    challenges = get_challenges()
    # Convert challenge_date_update to string format
    for challenge in challenges:
        challenge['challenge_date_update'] = str(challenge['challenge_date_update'])

    # Create DataFrame
    df = pd.DataFrame(challenges)
    return df

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
    if "challenge_id_to_edit"  not in st.session_state:
        st.session_state.challenge_id_to_edit = None
    if "challenge_df" not in st.session_state:
        st.session_state.challenge_df = get_challenges_df()
    if "transaction_status" not in st.session_state:
        st.session_state.transaction_status = False

    with st.sidebar:
        selected = option_menu("M8.Agenсy", ["Сотрудники", "Задания", "Награды", "Аналитика"],
                               icons=['house', "list-task", "award"], menu_icon="cast", default_index=0)
    # initialization of dataframes
    users_map = get_users_map()
    users_list = list(users_map.keys())
    if selected == "Сотрудники":
        st.subheader("Сотрудники")
        selected_user = st.selectbox(label="Cотрудник", index=None, placeholder='Выберите сотрудника',
                                     options=users_list)
        if selected_user:
            tab1, tab2 = st.tabs(["📈 Управление бонусами", "🗃 Управление задачами"])
            selected_user_name = users_map[selected_user]
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
                    user_account = get_user_bonus(selected_user_name)
                    metric_value = st.metric(label="Текущий баланс", value=user_account, delta=additional_bonus,
                              delta_color="normal", help=None, label_visibility="visible")
                if add_bonus:
                    new_balance = user_account + int(st.session_state.bonus_delta if operation == "Добавить"
                                                     else st.session_state.bonus_delta * (-1))
                    if update_value(collection="users", document=selected_user_name,
                                    field="user_free_bonuses", value=new_balance):
                        get_user_bonus.clear()
                        new_user_account = get_user_bonus(selected_user_name)
                        metric_value.metric(label="Текущий баланс", value=new_user_account, delta=additional_bonus,
                              delta_color="normal", help=None, label_visibility="visible")
                        print(f"Balance of {selected_user} updated")
                        st.success(f"Balance of {selected_user} updated")
                    else:
                        st.error("Operation failed")
    elif selected == "Задания":
        st.subheader("Управление заданиями")
        with st.expander(label="Добавление заданий в базу данных :new:", expanded=True):
            with st.form("new_challenge_form"):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_area(label="Задания", key="task_disc_widget",
                                 placeholder="Сформулируйте задание",
                                 max_chars=200, height=120)
                with col2:
                    st.number_input(label="Награда за выполнение",
                                    key="task_award_widget",
                                    min_value=0, value=None, step=1,
                                    placeholder="Введте колличество баллов")
                    st.number_input(label="Время на выполнение",
                                    key="task_planned_time_widget",
                                    min_value=0, value=None, step=1,
                                    placeholder="Введите количестов дней...")
                add_challenge_btn = st.form_submit_button(label="Добавить задание в базу", on_click=add_new_challenge,
                                                     use_container_width=True, type="primary")
                if add_challenge_btn:
                    if st.session_state.transaction_status:
                        st.success("Новое задание успешно создано")
                        st.session_state.transaction_status = False
                    else:
                        st.error("Не удалось создать новое задание")
        with st.expander(label="Редактирование задания :pencil2:"):
            challenges_df = st.session_state.challenge_df
            challenges_list = challenges_df['challenge_description'].tolist()
            challenge_id = None
            task_to_edit = st.selectbox(label="Задание", placeholder="Выберите задание для изменения",
                                        key="challenge_to_edit", options=challenges_list, index=None)
            with st.form("edit_challenge_form"):
                col1, col2 = st.columns(2)
                with col1:
                    if task_to_edit is None:
                        task_disc_to_edit = ""
                        task_award_to_edit = None
                        task_planned_time_to_edit = None
                    else:
                        challenge_id = \
                        challenges_df[challenges_df["challenge_description"] == task_to_edit]["id"].values[0]
                        selcted_challenge = challenges_df.loc[challenges_df["id"] == challenge_id]
                        task_disc_to_edit = selcted_challenge["challenge_description"].values[0]
                        task_award_to_edit = int(selcted_challenge["challenge_reward"].values[0])
                        task_planned_time_to_edit = int(selcted_challenge["challenge_planned_time_completion"].values[0])
                    st.text_area(value=task_disc_to_edit,
                                 label="Новое задание",
                                 key="edit_challenge_disc_widget",
                                 placeholder="Описание задания",
                                 max_chars=200, height=120)
                with col2:
                    st.number_input(value=task_award_to_edit,
                                    label="Новая награда за выполнение",
                                    key="edit_challenge_reward_widget",
                                    min_value=0, step=1,
                                    placeholder="Введте колличество баллов")
                    st.number_input(value=task_planned_time_to_edit,
                                    label="Новое время на выполнение",
                                    key="edit_challenge_planned_time_widget",
                                    min_value=0, step=1,
                                    placeholder="Введите количестов дней...")
                update_challenge_btn = st.form_submit_button(label="Применить изменения", on_click=update_table_update_challenge,
                                                             args=(challenge_id,), use_container_width=True, type="primary")
                if update_challenge_btn:
                    if st.session_state.transaction_status:
                        st.success("Задание успешно обновлено")
                        st.session_state.transaction_status = False
                    else:
                        st.error("Не удалось обновить задание")
        with st.expander(label="База заданийvenv :books:"):
            st.dataframe(st.session_state.challenge_df, use_container_width=False,
                         column_order=("challenge_description", "challenge_reward", "challenge_planned_time_completion",
                                       "challenge_active", "challenge_date_update"),
                         column_config={
                             "challenge_description": "Описание задания",
                             "challenge_reward": st.column_config.NumberColumn(label="Награда",
                                                                         help="Баллы за выполение задания",
                                                                         format="%d"),
                             "challenge_planned_time_completion": st.column_config.NumberColumn(label="Время на выполнение",
                                                                                           help="Количество дней, отведенное на выполнение задания",
                                                                                           format="%d"),
                             "challenge_active": st.column_config.CheckboxColumn(label="Задание в списке?",
                                                                            help="Здесь можно задание сделать доступным для выбора",
                                                                            default=False
                                                                            ),
                             "challenge_date_update": st.column_config.DateColumn(label="Дата обновления",
                                                                             help="Дата, когда задание было обновлено последний раз",
                                                                             format="DD.MM.YYYY")
                         },
                         hide_index=True
                         )