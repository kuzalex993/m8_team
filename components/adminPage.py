import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import date, timedelta, datetime


import logging

from components.firebase import get_credentials, get_users, update_value, get_challenges, add_new_document, update_document, get_rewards

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

def new_user_selected():
    if st.session_state.selected_user:
        selected_user_name = st.session_state.users_data_map[st.session_state.selected_user]
        st.session_state.current_user_balance = get_user_bonus(selected_user_name)

def update_user_bonus(user_name):
    st.session_state.bonus_delta = st.session_state.additional_bonus_widget

    new_balance = st.session_state.new_user_balance
    if update_value(collection="users", document=user_name,
                    field="user_free_bonuses", value=new_balance):
        st.session_state.transaction_status = True
    st.session_state.additional_bonus_widget = 0
    st.session_state.current_user_balance = get_user_bonus(user_name)


def add_new_reward():
    new_reward = {
        "reward_description": st.session_state.reward_description_widget,
        "reward_price": st.session_state.reward_price_widget
    }
    if add_new_document(collection_name="rewards", document_data=new_reward):
        st.session_state.transaction_status = True
    # clean text fields
    # st.session_state.reward_description_widget = None
    # st.session_state.reward_price_widget = None

    # retrieve updated data from firebase
    st.session_state.rewards_df = get_rewards_df()

def update_reward(reward_id):
    edited_reward = {
        "reward_description": st.session_state.edit_reward_description_widget,
        "reward_price": st.session_state.edit_reward_price_widget
    }
    if update_document(collection_name="rewards",
                       document_id=reward_id,
                       document_data=edited_reward):
        st.session_state.transaction_status = True


    # clean text fields
    # st.session_state.edit_reward_description_widget = None
    # st.session_state.edit_reward_price_widget = None

    # retrieve updated data from firebase
    st.session_state.rewards_df = get_rewards_df()

def add_new_challenge():
    new_task = {
        "challenge_description": st.session_state.task_description_widget,
        "challenge_reward": st.session_state.task_award_widget,
        "challenge_planned_time_completion": st.session_state.task_planned_time_widget,
        "challenge_active": True,
        "challenge_date_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }
    if add_new_document(collection_name="challenges", document_data=new_task):
        st.session_state.transaction_status = True

    # clean text fields
    # st.session_state.task_description_widget = None
    # st.session_state.task_award_widget = None
    # st.session_state.task_planned_time_widget = None

    # retrieve updated data from firebase
    st.session_state.challenge_df = get_challenges_df()


def update_challenge(challenge_id):
    edited_task = {
        "challenge_description": st.session_state.edit_challenge_description_widget,
        "challenge_reward": st.session_state.edit_challenge_reward_widget,
        "challenge_planned_time_completion": st.session_state.edit_challenge_planned_time_widget,
        "challenge_active": True,
        "challenge_date_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }
    if update_document(collection_name="challenges",
                       document_id=challenge_id,
                       document_data=edited_task):
        st.session_state.transaction_status = True


    # clean text fields
    # st.session_state.challenge_to_edit = None
    # st.session_state.edit_challenge_description_widget = None
    # st.session_state.edit_challenge_reward_widget = None
    # st.session_state.edit_challenge_planned_time_widget = None

    # retrieve updated data from firebase
    st.session_state.challenge_df = get_challenges_df()

def get_user_bonus(selected_user_name: str) -> int:
    users_data = get_users()
    user_account = int(users_data[selected_user_name]["user_free_bonuses"])
    return user_account


def get_users_map() -> dict():
    cred = st.session_state.users_config
    fire_users = cred["credentials"]["usernames"]
    for key, value in fire_users.items():
        if key != "admin":
            user_map[value["name"]] = key
    return user_map


def get_challenges_df():
    challenges = get_challenges()
    # Convert challenge_date_update to string format
    for challenge in challenges:
        challenge['challenge_date_update'] = str(challenge['challenge_date_update'])

    # Create DataFrame
    df = pd.DataFrame(challenges)
    return df

def get_rewards_df():
    rewards = get_rewards()
    df = pd.DataFrame(rewards)
    return df


def show_admin_page():
    # initialize session variables
    if "task_description" not in st.session_state:
        st.session_state.task_description = ""
        st.session_state.task_award = ""
        st.session_state.task_planned_time = ""
    if "reward_description" not in st.session_state:
        st.session_state.reward_description = ""
        st.session_state.reward_price = ""
    if "bonus_delta" not in st.session_state:
        st.session_state.bonus_delta = None
    if "challenge_df" not in st.session_state:
        st.session_state.challenge_df = get_challenges_df()
    if "rewards_df" not in st.session_state:
        st.session_state.rewards_df = get_rewards_df()
    if "transaction_status" not in st.session_state:
        st.session_state.transaction_status = False
    if "users_data_map" not in st.session_state:
        st.session_state.users_data_map = get_users_map()

    # to check if wee need these variables in session_state
    if "new_user_balance" not in st.session_state:
        st.session_state.new_user_balance = None
    if "current_user_balance" not in st.session_state:
        st.session_state.current_user_balance = None

    with st.sidebar:
        selected = option_menu("M8.Agenсy", ["Сотрудники", "Задания", "Награды", "Аналитика"],
                               icons=['house', "list-task", "award"], menu_icon="cast", default_index=0)
    if selected == "Сотрудники":
        st.subheader("Сотрудники")
        users_list = list(st.session_state.users_data_map.keys())
        selected_user = st.selectbox(label="Cотрудник", index=None, placeholder='Выберите сотрудника', key="selected_user",
                                     on_change=new_user_selected, options=users_list)
        if selected_user:
            selected_user_name = st.session_state.users_data_map[selected_user]
            tab1, tab2 = st.tabs(["📈 Управление бонусами", "🗃 Управление задачами"])
            with tab1:
                with st.container():
                    col1, col2 = st.columns(2)
                    additional_bonus = 0
                    with col1:
                        additional_bonus = st.number_input(label="Бонусы", value=0, placeholder="Введите количество бонусов",
                                                           key="additional_bonus_widget")
                        operation = st.radio(label="Операция", options=["Добавить", "Вычесть"], horizontal=True)
                        if operation == "Вычесть":
                            additional_bonus *= (-1)
                    with col2:
                        metric_value = st.metric(label="Текущий баланс", value=st.session_state.current_user_balance,
                                                 delta=None if additional_bonus==0 else additional_bonus,
                                                 delta_color="normal", help=None, label_visibility="visible")
                        st.session_state.new_user_balance = st.session_state.current_user_balance + additional_bonus
                    add_bonus = st.button("Изменить баланс", on_click=update_user_bonus, args=(selected_user_name,),
                                          use_container_width=True, type="primary")

                    if add_bonus:
                        if st.session_state.transaction_status:
                            st.success(f"Баланс пользователя {selected_user} обновлен")
                            st.session_state.transaction_status = False
                        else:
                            st.error("Не удалось обновить баланс")
    elif selected == "Задания":
        st.subheader("Управление заданиями")
        with st.expander(label="Добавление заданий в базу данных :new:", expanded=True):
            with st.form("add_challenge_form"):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_area(label="Задания", key="task_description_widget",
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
                        task_description_to_edit = ""
                        task_award_to_edit = None
                        task_planned_time_to_edit = None
                    else:
                        challenge_id = \
                        challenges_df[challenges_df["challenge_description"] == task_to_edit]["id"].values[0]
                        selcted_challenge = challenges_df.loc[challenges_df["id"] == challenge_id]
                        task_description_to_edit = selcted_challenge["challenge_description"].values[0]
                        task_award_to_edit = int(selcted_challenge["challenge_reward"].values[0])
                        task_planned_time_to_edit = int(selcted_challenge["challenge_planned_time_completion"].values[0])
                    st.text_area(value=task_description_to_edit,
                                 label="Новое задание",
                                 key="edit_challenge_description_widget",
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
                update_challenge_btn = st.form_submit_button(label="Применить изменения", on_click=update_challenge,
                                                             args=(challenge_id,), use_container_width=True, type="primary")
                if update_challenge_btn:
                    if st.session_state.transaction_status:
                        st.success("Задание успешно обновлено")
                        st.session_state.transaction_status = False
                    else:
                        st.error("Не удалось обновить задание")
        with st.expander(label="База заданий :books:"):
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
    elif selected == "Награды":
        st.subheader("Управление наградами")
        with st.expander(label="Добавить новую награду :new:", expanded=True):
            with st.form("add_reward_form"):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_area(label="Награда", key="reward_description_widget",
                                 placeholder="Добавьте описание награды",
                                 max_chars=200)
                with col2:
                    st.number_input(label="Стоимость награды",
                                    key="reward_price_widget",
                                    min_value=0, value=None, step=1,
                                    placeholder="Введте колличество баллов")
                add_reward_btn = st.form_submit_button(label="Добавить награду в базу", on_click=add_new_reward,
                                                     use_container_width=True, type="primary")
                if add_reward_btn:
                    if st.session_state.transaction_status:
                        st.success("Новая награда успешно создана")
                        st.session_state.transaction_status = False
                    else:
                        st.error("Не удалось создать новую награду")
        with st.expander(label="Редактирование награды :pencil2:"):
            rewards_df = st.session_state.rewards_df
            rewards_list = rewards_df['reward_description'].tolist()
            reward_id = None
            reward_to_edit = st.selectbox(label="Награда", placeholder="Выберите награду для изменения",
                                        key="reward_to_edit", options=rewards_list, index=None)
            with st.form("edit_reward_form"):
                col1, col2 = st.columns(2)
                with col1:
                    if reward_to_edit is None:
                        reward_description_to_edit = ""
                        reward_price_to_edit = None
                    else:
                        reward_id = \
                        rewards_df[rewards_df["reward_description"] == reward_to_edit]["id"].values[0]
                        selcted_reward = rewards_df.loc[rewards_df["id"] == reward_id]
                        reward_description_to_edit = selcted_reward["reward_description"].values[0]
                        reward_price_to_edit = int(selcted_reward["reward_price"].values[0])
                    st.text_area(value=reward_description_to_edit,
                                 label="Новая нраграда",
                                 key="edit_reward_description_widget",
                                 placeholder="Новое опасание нраграды",
                                 max_chars=200)
                with col2:
                    st.number_input(value=reward_price_to_edit, 
                                    label="Новая стоимость награды",
                                    key="edit_reward_price_widget",
                                    min_value=0, step=1,
                                    placeholder="Введте колличество баллов")

                update_reward_btn = st.form_submit_button(label="Применить изменения", on_click=update_reward,
                                                             args=(reward_id,), use_container_width=True, type="primary")
                if update_reward_btn:
                    if st.session_state.transaction_status:
                        st.success("Награда успешно обновлена")
                        st.session_state.transaction_status = False
                    else:
                        st.error("Не удалось обновить награду")