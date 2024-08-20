import pandas as pd
import os
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
load_dotenv()


import logging

from components.firebase import (put_into_user_bonus_collection, put_into_user_challenge_collection,
                                 get_document, get_value,
                                 get_users, update_value, add_new_document,
                                 get_collection, update_document, get_user_rewards)
from components.notifications import send_message



transaction_type_map = {
    "Добавить": "charge bonus",
    "Вычесть": "write off bonus",
    "Зарезирвировать": "reserve bonus"
}



def new_user_selected():
    if st.session_state.selected_user_name:
        selected_user_id = st.session_state["users_data_map"][st.session_state["selected_user_name"]]
        st.session_state["current_user_balance"] = get_user_bonus(selected_user_id)

def notify_user(message: str, user_name: str):
    user_chat_id = get_value(collection_name="users",document_name=user_name,field_name="chat_id")
    send_message(chat_id=user_chat_id, text=message)

def update_user_bonus(user_name):
    additional_bonus = st.session_state.additional_bonus_widget
    transaction_type = transaction_type_map[st.session_state.operation_widget]
    if transaction_type == "write off bonus":
        additional_bonus *= (-1)
    if put_into_user_bonus_collection(user_id=user_name, transaction_type=transaction_type,
                                    bonus_value=additional_bonus,
                                    event_type="admin",event_id="None"):
        if update_value(collection="users", document=user_name,
                        field="user_free_bonuses", value=st.session_state.new_user_balance):
            if additional_bonus > 0:
                notify_user(message=f"Администратор добавил вам {additional_bonus} бонусов", user_name=user_name)
            elif additional_bonus < 0:
                notify_user(message=f"Администратор уменьшил ваш баланс на {additional_bonus} бонусов", user_name=user_name)
            st.session_state.transaction_status = True
        st.session_state.additional_bonus_widget = 0
    st.session_state.current_user_balance = get_user_bonus(user_name)


def add_new_reward():
    new_reward = {
        "reward_description": st.session_state.reward_description_widget,
        "reward_price": st.session_state.reward_price_widget,
        "reward_last_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }
    if add_new_document(collection_name="rewards", document_data=new_reward):
        st.session_state.transaction_status = True

    # retrieve updated data from firebase
    st.session_state.rewards_df = get_rewards_df()        

def update_reward(reward_id):
    edited_reward = {
        "reward_description": st.session_state.edit_reward_description_widget,
        "reward_price": st.session_state.edit_reward_price_widget,
        "reward_last_update": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }
    if update_document(collection_name="rewards",
                       document_id=reward_id,
                       document_data=edited_reward):
        st.session_state.transaction_status = True

    # retrieve updated data from firebase
    st.session_state.rewards_df = get_rewards_df()

def add_new_user_challenge(challenge_id: int, challenge_duration: int):
    if st.session_state.selected_user_name:
        selected_user_id = st.session_state.users_data_map[st.session_state.selected_user_name]
        print(st.session_state.challenge_to_assign_start_date_widget)
        status = put_into_user_challenge_collection(user_id=selected_user_id, user_name=st.session_state.selected_user_name,
                                                    challenge_id=challenge_id,
                                                    challenge_descripion=st.session_state.challenge_to_assign_description_widget,
                                                    start_date=st.session_state.challenge_to_assign_start_date_widget,
                                                    challenge_duration=challenge_duration,
                                                    challenge_creation_date=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ") 
                                                    )
        if status:
            notify_user(message=f"Вам назначено новое задание:\nОписание: {st.session_state.challenge_to_assign_description_widget}\nДата начала: {st.session_state.challenge_to_assign_start_date_widget}\nВремя на выполнение: {challenge_duration} дней",
                        user_name=selected_user_id)
            st.session_state.transaction_status = True
            # retrieve updated data from firebase
            st.session_state.user_challenge_df = get_user_challenge_df()

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

    # retrieve updated data from firebase
    st.session_state.challenge_df = get_challenges_df()


def update_challenge(challenge_id):
    edited_task = {
        "challenge_description": st.session_state.edit_challenge_description_widget,
        "challenge_reward": st.session_state.edit_challenge_reward_widget,
        "challenge_planned_time_completion": st.session_state.edit_challenge_planned_time_widget,
        "challenge_active": True,
        "challenge_date_update": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }
    if update_document(collection_name="challenges",
                       document_id=challenge_id,
                       document_data=edited_task):
        st.session_state.transaction_status = True

    # retrieve updated data from firebase
    st.session_state.challenge_df = get_challenges_df()

def get_user_bonus(selected_user_id: str) -> int:
    users_data = get_users()
    user_account = int(users_data[selected_user_id]["user_free_bonuses"])
    return user_account


def get_users_map() -> dict:
    user_map = dict()
    users = get_users()
    for key, value in users.items():
        if key != "admin" and key != "alekseik":
            user_map[value["user_name"]] = key
    return user_map


def get_challenges_df():
    challenges = get_collection(collection_name="challenges")
    # Convert challenge_date_update to string format
    for challenge in challenges:
        challenge['challenge_date_update'] = str(challenge['challenge_date_update'])
    # Create DataFrame
    df = pd.DataFrame(challenges)
    return df

def get_rewards_df():
    rewards = get_collection(collection_name="rewards")
    df = pd.DataFrame(rewards)
    return df

def get_user_challenge_df():
    user_challenge = get_collection(collection_name="user_challenge")
    df = pd.DataFrame(user_challenge)
    return df

def confirm_user_request(user_reward_id: str, user_id: str, reward_id: str):
    reward_price = get_value(collection_name="rewards",document_name=reward_id, field_name="reward_price")
    reward_description = get_value(collection_name="rewards",document_name=reward_id, field_name="reward_description")
    user_reserved_bonus = get_value(collection_name="users",document_name=user_id, field_name="user_reserved_bonuses")
    if reward_price > user_reserved_bonus:
        print("Error! Lack of reserved bonuses")
    else:
        updated_user_data = {
            "user_reserved_bonuses": user_reserved_bonus - reward_price
        }
        update_document(collection_name="users", document_id=user_id, document_data=updated_user_data)
        updated_user_reward_data = {
            "user_reward_status": "completed",
            "user_reward_decision_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
        update_document(collection_name="user_reward", document_id=user_reward_id, document_data=updated_user_reward_data)
        new_user_bonus_record = {
            "user_id": user_id,
            "transaction_type": "debiting bonus",
            "event_type": "user_reward",
            "event_id": user_reward_id,
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "bonus_value": reward_price
        }
        add_new_document(collection_name="user_bonus", document_data=new_user_bonus_record)
        notify_user(message=f"Ура! Админ подтвердил награду: {reward_description}",
                    user_name=user_id)


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
    if "user_challenge_df" not in st.session_state:
        st.session_state.user_challenge_df = get_user_challenge_df()
    if "transaction_status" not in st.session_state:
        st.session_state.transaction_status = False
    if "users_data_map" not in st.session_state:
        st.session_state.users_data_map = get_users_map()
    if "bot_endpoint" not in st.session_state:
        st.session_state["bot_endpoint"] = os.getenv("T_BOT_ENDPOINT")

    # to check if wee need these variables in session_state
    if "new_user_balance" not in st.session_state:
        st.session_state.new_user_balance = None
    if "current_user_balance" not in st.session_state:
        st.session_state.current_user_balance = None

    with st.sidebar:
        selected = option_menu("M8.Agenсy", ["Сотрудники", "Задания", "Награды", "Запросы"],
                               icons=['house', "list-task", "award"], menu_icon="cast", default_index=0)
    if selected == "Сотрудники":
        st.subheader("Сотрудники")
        st.session_state["users_data_map"] = get_users_map()
        users_list = list(st.session_state["users_data_map"].keys())
        selected_user_name = st.selectbox(label="Cотрудник", index=None, placeholder='Выберите сотрудника', key="selected_user_name",
                                     on_change=new_user_selected, options=users_list)
        if selected_user_name:
            selected_user_id = st.session_state["users_data_map"][selected_user_name]
            tab1, tab2 = st.tabs(["📈 Управление бонусами пользователей", "🗃 Управление заданиями пользователей"])
            with tab1:
                with st.container():
                    col1, col2 = st.columns(2)
                    additional_bonus = 0
                    with col1:
                        additional_bonus = st.number_input(label="Бонусы", value=0, placeholder="Введите количество бонусов",
                                                           key="additional_bonus_widget")
                        operation = st.radio(label="Операция", options=["Добавить", "Вычесть"], 
                                             horizontal=True, key="operation_widget")
                        if operation == "Вычесть":
                            additional_bonus *= (-1)
                    with col2:
                        st.metric(label="Текущий баланс", 
                                  value=st.session_state.current_user_balance,
                                  delta=None if additional_bonus==0 else additional_bonus,
                                  delta_color="normal", help=None, label_visibility="visible")
                        st.session_state.new_user_balance = st.session_state.current_user_balance + additional_bonus
                    if st.session_state.new_user_balance < 0:
                        st.warning("Надостаточно текущего баланса для совершения операции")
                    else:
                        add_bonus = st.button("Изменить баланс", on_click=update_user_bonus, args=(selected_user_id,),
                                          use_container_width=True, type="primary")
                        if add_bonus:
                            if st.session_state.transaction_status:
                                st.success(f"Баланс пользователя {selected_user_name} обновлен")
                                st.session_state.transaction_status = False
                            else:
                                st.error("Не удалось обновить баланс")
            with tab2:
                challenges_list = st.session_state.challenge_df['challenge_description'].tolist()
                col1, col2, col3, col4 = st.columns([3,1,1,1])
                selected_challenge = None
                with col1:
                    challenge_to_assign = st.selectbox(label="Задание", placeholder="Выберите задание",
                                                    key="challenge_to_assign_description_widget", options=challenges_list, index=0)
                    challenge_id = \
                        st.session_state.challenge_df[st.session_state.challenge_df["challenge_description"] == challenge_to_assign]["id"].values[0]
                    selected_challenge = st.session_state.challenge_df.loc[st.session_state.challenge_df["id"] == challenge_id]
                    challenge_duration = int(selected_challenge["challenge_planned_time_completion"].values[0])
                    challenge_reward = int(selected_challenge["challenge_reward"].values[0])    
                with col2:
                    start_date = st.date_input(label="Дата начала", key="challenge_to_assign_start_date_widget",
                                               format="DD/MM/YYYY")
                with col3:
                    planned_finish_date = st.date_input(label="Дата окончания", disabled = True,
                                                        value=start_date + timedelta(days=challenge_duration),
                                                        format="DD/MM/YYYY")
                with col4:    
                    st.number_input(label="Бонусы", value=challenge_reward, disabled=True)
                    
                if selected_challenge is not None:
                    assign_challenge_btn = st.button(label="Назначить задание", use_container_width=True,
                                                     type="primary", on_click=add_new_user_challenge, args=(challenge_id, challenge_duration))
                    if assign_challenge_btn:
                        if st.session_state.transaction_status:
                            st.success(f"Задание **{challenge_to_assign}** назначено пользователю **{selected_user_name}**")
                            st.session_state.transaction_status = False
                        else:
                            st.error("Не удалось назначить задание")
                st.divider()
                with st.container():
                    current_user_challenge_df = st.session_state.user_challenge_df\
                        .loc[(st.session_state.user_challenge_df["user_name"]==selected_user_name) & (st.session_state.user_challenge_df["challenge_status"]!="complete")]
                    if current_user_challenge_df.shape[0] == 0:
                        st.info(f"Пользователь {selected_user_name} пока не имеет открытых заданий")
                    else:
                        st.dataframe(current_user_challenge_df, use_container_width=False,
                                    column_order=("challenge_descripion", "start_date", "planned_finish_date",
                                                "challenge_status","fact_finish_date","challenge_success"),
                                                column_config={
                                                                "challenge_descripion": "Описание задания",
                                                                "start_date": st.column_config.DateColumn(label="Дата начала",
                                                                                                            format="DD/MM/YYYY"),
                                                                "planned_finish_date": st.column_config.DateColumn(label="Дата окончания",
                                                                                                                    format="DD/MM/YYYY"),
                                                                "challenge_status": st.column_config.TextColumn(label="Статус задания",
                                                                                                                default=False),
                                                                "fact_finish_date": st.column_config.DateColumn(label="Фактическая дата завершения",
                                                                                                                format="DD.MM.YYYY"),
                                                                "challenge_success": st.column_config.TextColumn(label="Успех прохождения",
                                                                                                                default=False),                                                                                                
                                                                                                
                            },
                            hide_index=True
                            )
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
                                    placeholder="Введите колличество баллов")
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
                        selected_challenge = challenges_df.loc[challenges_df["id"] == challenge_id]
                        task_description_to_edit = selected_challenge["challenge_description"].values[0]
                        task_award_to_edit = int(selected_challenge["challenge_reward"].values[0])
                        task_planned_time_to_edit = int(selected_challenge["challenge_planned_time_completion"].values[0])
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
                                    placeholder="Введите колличество баллов")
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
                                    placeholder="Введите колличество баллов")
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
                                 label="Новая награда",
                                 key="edit_reward_description_widget",
                                 placeholder="Новое опасание награды",
                                 max_chars=200)
                with col2:
                    st.number_input(value=reward_price_to_edit, 
                                    label="Новая стоимость награды",
                                    key="edit_reward_price_widget",
                                    min_value=0, step=1,
                                    placeholder="Введите колличество баллов")

                update_reward_btn = st.form_submit_button(label="Применить изменения", on_click=update_reward,
                                                             args=(reward_id,), use_container_width=True, type="primary")
                if update_reward_btn:
                    if st.session_state.transaction_status:
                        st.success("Награда успешно обновлена")
                        st.session_state.transaction_status = False
                    else:
                        st.error("Не удалось обновить награду")
        with st.expander(label="База наград :books:"):
            st.dataframe(st.session_state.rewards_df, use_container_width=False,
                         column_order=("reward_description", "reward_price", "reward_last_update"),
                         column_config={
                             "reward_description": "Описание награды",
                             "reward_price": st.column_config.NumberColumn(label="Стоимость награды",
                                                                         help="Стоимость в баллах",
                                                                         format="%d"),
                             "reward_last_update": st.column_config.DateColumn(label="Дата обновления",
                                                                             help="Дата, когда награда была обновлена последний раз",
                                                                             format="DD.MM.YYYY")
                         },
                         hide_index=True
                         )
    elif selected == "Запросы":
        user_rewards = get_user_rewards(user_id="all")
        completed_rewards_to_df = {
            "name": [],
            "description": [],
            "request_date": [],
            "status": [],
            "decision_date": []
            }
        show_info_flag = True
        info_messages = ["Ого! Кажется, пока тут пусто...", "И тут тоже пусто..."]
        for user_reward in user_rewards:
            current_reward = user_reward.to_dict()
            if current_reward["user_reward_status"] == "new":
                show_info_flag = False        
                with st.form(f"request_form_{user_reward.id}"):
                    request_col1, request_col2, request_col3, request_col4 = st.columns([2,1,1,1])
                    requester_id = current_reward["user_id"]
                    requester_name = current_reward["user_name"]
                    reward_id = current_reward["reward_id"]
                    date_object = datetime.fromisoformat(current_reward["user_reward_request_date"].replace("Z", "+00:00"))
                    formatted_date = date_object.strftime("%d/%m/%Y")
                    with request_col1:
                        st.markdown( body= f"{current_reward['reward_description']}")
                    with request_col2:    
                        st.caption(body=f"{requester_name}")
                    with request_col3:
                        st.caption(body=f"{formatted_date}")  
                    with request_col4:
                        st.form_submit_button(label="Подтвердить", use_container_width=True, type="primary",
                                            on_click=confirm_user_request,
                                            args=(user_reward.id, requester_id, reward_id,))
            else:
                completed_rewards_to_df["description"].append(current_reward["reward_description"])
                completed_rewards_to_df["name"].append(current_reward["user_name"])
                completed_rewards_to_df["request_date"].append(current_reward["user_reward_request_date"])
                completed_rewards_to_df["status"].append(current_reward["user_reward_status"])
                completed_rewards_to_df["decision_date"].append(current_reward["user_reward_decision_date"])
        if show_info_flag:
            st.info(info_messages[0])
            info_messages.pop(0)
        with st.expander("Остальные запросы"):
            if len(completed_rewards_to_df["description"]) == 0:
                st.info(info_messages[0])
            else:
                completed_rewards_df = pd.DataFrame(completed_rewards_to_df).sort_values(by="request_date",
                                                                                         ascending=False)
                st.dataframe(completed_rewards_df, use_container_width=True,
                            column_order=("description", "name", "request_date","status", "decision_date"),
                            column_config={
                                "description": "Описание награды",
                                "name": "Имя",
                                "request_date": st.column_config.DateColumn(label="Дата запроса", format="DD.MM.YYYY"),
                                "status": "Статус запроса",
                                "decision_date": st.column_config.DateColumn(label="Дата принятия решения", format="DD.MM.YYYY")
                                },
                                hide_index=True
                            )    