import streamlit as st
from dotenv import load_dotenv
import os
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
from streamlit_echarts import st_echarts
from datetime import datetime, timedelta
import pandas as pd

load_dotenv()

from components.firebase import (get_document, get_user_challenges, get_collection, get_value,
                                 put_into_user_bonus_collection, 
                                 put_into_user_challenge_collection,
                                 get_users, update_value, add_new_document,
                                 update_document, get_user_rewards)

from components.notifications import send_message


def draw_bonus_chart(_free_bonus: int, _reserved_bonus: int) -> dict:
    options = {
        "tooltip": {"trigger": "item"},
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
                "labelLine": {"show": False},
                "data": [
                    {"value": _free_bonus, "name": "Доступно"},
                    {"value": _reserved_bonus, "name": "Резерв"}
                ],
            }
        ],
    }
    return options

def update_user_challenges_status(id_list: list)->bool:
    for id in id_list:
        update_value(collection="user_challenge",document=id, field="challenge_status", value="ongoing")
def refresh_user_data():
    st.session_state.user_data = get_document(collection_name="users",document_name=st.session_state.user_id)

def notify_admin(message: str):
    admin_chat_id = get_value(collection_name="users",document_name="admin",field_name="chat_id")
    send_message(chat_id=admin_chat_id, text=message)


def get_challenges_df():
    challenges = get_collection(collection_name="challenges")
    for challenge in challenges:
        challenge['challenge_date_update'] = str(challenge['challenge_date_update'])
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


def request_reward(reward_id: str, reward_description: str, reward_price: int):
    user_reserved_bonus = get_value(collection_name="users",document_name=st.session_state.username, field_name="user_reserved_bonuses")
    user_free_bonuses = get_value(collection_name="users",document_name=st.session_state.username, field_name="user_free_bonuses")
    new_user_reward_record = {
        "reward_description": reward_description,
        "reward_id": reward_id,
        "user_id": st.session_state.username,
        "user_name": st.session_state.user_data["user_name"],
        "user_reward_decision_date": None,
        "user_reward_request_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "user_reward_status": "new"
    }
    user_reward_id = add_new_document(collection_name="user_reward", document_data=new_user_reward_record)

    updated_user_data = {
            "user_free_bonuses": user_free_bonuses - reward_price,
            "user_reserved_bonuses": user_reserved_bonus + reward_price
        }
    update_document(collection_name="users", document_id=st.session_state.username, document_data=updated_user_data)
    if user_reward_id is not None:
        new_user_bonus_record = {
                "bonus_value": reward_price,
                "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "event_id": user_reward_id,
                "event_type": "user_reward",
                "transaction_type": "reserve bonus",
                "user_id": st.session_state.username
            }
        new_user_bonus_record_id = add_new_document(collection_name="user_bonus", document_data=new_user_bonus_record)
    else:
        print(f"Returned user_reward_id is 'None'. There was an issue to create new record in user_reward collection")
    notify_admin(message=f"Запрошена новая награда:\nПользователь: {st.session_state.user_data['user_name']} \nНаграда: {reward_description}")
    refresh_user_data()

def add_new_user_challenge(challenge_id: int, challenge_duration: int):
    put_into_user_challenge_collection(user_id=st.session_state.username, 
                                        user_name=st.session_state.user_data["user_name"],
                                        challenge_id=challenge_id,
                                        challenge_descripion=st.session_state.challenge_to_assign_description_widget,
                                        start_date=st.session_state.challenge_to_assign_start_date_widget,
                                        challenge_duration=challenge_duration,
                                        challenge_creation_date=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ") 
                                        )

def close_user_challenge(id):
    if st.session_state['panned_finish_'+id] >= datetime.now().date():
        challenge_id = get_value(collection_name="user_challenge",document_name=id,field_name="challenge_id")
        challenge_reward = get_value(collection_name="challenges",document_name=challenge_id,field_name="challenge_reward")
        current_user_bonus = get_value(collection_name="users",document_name=st.session_state.username,
                                       field_name="user_free_bonuses")
        new_user_bonus = current_user_bonus + challenge_reward
        new_user_bonus_record = {
            "bonus_value": challenge_reward,
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "event_id": id,
            "event_type": "user_challenge",
            "transaction_type": "charge bonus",
            "user_id": st.session_state.username
        }
        update_value(collection="users",document=st.session_state.username,
                        field="user_free_bonuses", value=new_user_bonus)
        new_user_bonus_record_id = add_new_document(collection_name="user_bonus", document_data=new_user_bonus_record)
        new_challenges(message=f"Задание закрыто вовремя. Начислено {challenge_reward} бонусов")

        updated_user_challenge_data = {
            "fact_finish_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "challenge_status":"finished",
            "challenge_success": True
        }
    else:
        new_challenges("Очень жаль, но бонусы не будут начислены. Задание закрыто с опозданием.")
        updated_user_challenge_data = {
            "fact_finish_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "challenge_status": "finished",
            "challenge_success": False

        }

    update_document(collection_name="user_challenge", document_id=id, document_data=updated_user_challenge_data)
    refresh_user_data()

@st.experimental_dialog("Задание закрыто")
def new_challenges(message: str):
    st.write(message)



def show_user_page():
    if "free_bonus" not in st.session_state:
        st.session_state.user_data['user_free_bonuses'] = None
    if "reserved_bonus" not in st.session_state:
        st.session_state.user_data['user_reserved_bonuses'] = None
    if "user_data" not in st.session_state:
        st.session_state["user_data"] = get_document(collection_name="users", document_name=st.session_state.user_id)
    if "bot_endpoint" not in st.session_state:
        st.session_state["bot_endpoint"] = os.getenv("T_BOT_ENDPOINT")
    
    with st.sidebar:
        selected = option_menu("M8Agency", ["Мои бонусы", "Мои задания", "Мои настройки"],
                               icons=["award", "list-task",], menu_icon="cast", default_index=0)

    if selected=="Мои бонусы":
        st.session_state["user_data"] = get_document(collection_name="users", 
                                                     document_name=st.session_state["user_id"])
        with st.container(height=300, border=True):
            col1, col2 = st.columns(2)
            with col1:
                st.header(st.session_state.user_data["user_name"], anchor=None,  help=None, divider=False)
                st.markdown(f"**Позиция:** {st.session_state.user_data['user_position']}", help=None)
                st.markdown(f"**Доступные бонусы:** {st.session_state.user_data['user_free_bonuses']}", help=None)
                st.markdown(f"**Бонусы в резерве:** {st.session_state.user_data['user_reserved_bonuses']}", help=None)
            with col2:
                chart_options = draw_bonus_chart(_free_bonus=st.session_state.user_data["user_free_bonuses"], 
                                                 _reserved_bonus=st.session_state.user_data["user_reserved_bonuses"])
                st_echarts(options=chart_options, height="250px")
        with st.expander("Выбрать награду", expanded=False):
            rewards_df =  get_rewards_df()
            rewards_list = rewards_df['reward_description'].tolist()
            reward_id = None
            reward_to_get = st.selectbox(label="Награда", placeholder="Выберите желаемую награду",
                                        key="reward_to_get", options=rewards_list, index=None)
            if reward_to_get is not None:
                reward_id = \
                rewards_df[rewards_df["reward_description"] == reward_to_get]["id"].values[0]
                selcted_reward = rewards_df.loc[rewards_df["id"] == reward_id]
                reward_price = int(selcted_reward["reward_price"].values[0])
                
                if st.session_state.user_data["user_free_bonuses"] >= reward_price:
                    col1, col2 = st.columns(2)
                    with col1:
                            st.info(f"Стоимость награды: **{reward_price}** баллов")
                    with col2:
                        st.button(label="Получить награду", on_click=request_reward,
                                  args=(reward_id, reward_to_get,reward_price,),
                                  use_container_width=True, type="primary")
                else:
                    st.warning(f"У вас недостаточно баллов, чтобы получить награду. Стоимость награды **{reward_price}**")
        with st.expander("Запрошенные награды", expanded=False):
            user_rewards = get_user_rewards(user_id=st.session_state.username)
            to_rewards_df = {
                "description": [],
                "request_date": [],
                "status": []
                }
            for reward in user_rewards:
                current_reward = reward.to_dict()
                request_date = datetime.strptime(current_reward["user_reward_request_date"], "%Y-%m-%dT%H:%M:%S.%fZ")
                to_rewards_df["description"].append(current_reward["reward_description"])
                to_rewards_df["request_date"].append(request_date)
                to_rewards_df["status"].append(current_reward["user_reward_status"])
                rewards_df = pd.DataFrame(to_rewards_df).sort_values(by="request_date", ascending=False)
            st.dataframe(data=rewards_df, use_container_width=True, hide_index=True,
                         column_order=["description","request_date", "status"], column_config={
                             "description": st.column_config.Column(label="Награда"),
                             "request_date": st.column_config.DatetimeColumn(label="Дата запроса"),
                             "status": st.column_config.Column(label="Статус запроса")
                             })
    elif selected=="Мои задания":
        with st.expander("Выбрать новое задание", expanded=False):
            st.session_state.challenge_df = get_challenges_df()
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
                st.button(label="Назначить задание", use_container_width=True,
                          type="primary", on_click=add_new_user_challenge, args=(challenge_id, challenge_duration))
        with st.container():
            user_challenges_new = get_user_challenges(user_id=st.session_state.user_id,
                                                      challenge_status="new")
            new_challenges_ids = []
            for challenge in user_challenges_new:
                with st.form(f"challenge_form_{challenge.id}"):
                    challenge_cur = challenge.to_dict()
                    new_challenges_ids.append(challenge.id)
                    st.markdown( body= f"**:new:** {challenge_cur['challenge_descripion']}")
                    creation_date = challenge_cur["challenge_creation_date"]
                    st.caption(body=f"Задание добавленo: {creation_date}")
                    col1, col2 = st.columns([1,1])                    
                    with col1:
                        start_date=datetime.strptime(challenge_cur["start_date"], '%Y-%m-%d')
                        st.date_input(label="Начало", value=start_date, format="DD/MM/YYYY", key=f"start_{challenge.id}", disabled=True)
                    with col2:
                        if challenge_cur["planned_finish_date"] is None:
                            end_date = None
                        else:
                            end_date=datetime.strptime(challenge_cur["planned_finish_date"], '%Y-%m-%d')
                        st.date_input(label="Окончание", value=end_date, format="DD/MM/YYYY", 
                                      key=f"panned_finish_{challenge.id}", disabled=True)

                    st.form_submit_button(label="Завершить", use_container_width=True,
                                              type="secondary", on_click=close_user_challenge,
                                              args=(challenge.id,))
            with st.container():
                user_challenges_ongoing = get_user_challenges(user_id=st.session_state.user_id,
                                                            challenge_status="ongoing")
                for challenge in user_challenges_ongoing:
                    with st.form(f"challenge_form_{challenge.id}"):
                        challenge_cur = challenge.to_dict()
                        st.markdown(body=challenge_cur["challenge_descripion"])
                        col1, col2 = st.columns([1,1])                    
                        with col1:
                            start_date=datetime.strptime(challenge_cur["start_date"], '%Y-%m-%d')
                            st.date_input(label="Начало", value=start_date,
                                          format="DD/MM/YYYY", key=f"start_{challenge.id}", 
                                          disabled=True)
                        with col2:
                            if challenge_cur["planned_finish_date"] is None:
                                end_date = None
                            else:
                                end_date=datetime.strptime(challenge_cur["planned_finish_date"], '%Y-%m-%d')
                            st.date_input(label="Окончание", value=end_date, 
                                          format="DD/MM/YYYY", key=f"panned_finish_{challenge.id}",
                                          disabled=True)

                        st.form_submit_button(label="Завершить", use_container_width=True,
                                              type="secondary", on_click=close_user_challenge,
                                              args=(challenge.id,))
            # we update new challenges status after all challenges are displayed,
            update_user_challenges_status(id_list=new_challenges_ids)
    elif selected=="Мои настройки":
        st.markdown(body="Для того, чтобы подключить уведомления, перейдите по ссылке в Telegram бот.")
        st.markdown(f"[Перейти в Телеграм web](https://web.telegram.org/k/#@EightAgencyAssist_bot)")
        st.markdown(f"[Перейти в Телеграм app]({st.session_state['bot_endpoint']})")