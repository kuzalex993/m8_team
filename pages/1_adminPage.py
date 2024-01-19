import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_gsheets import GSheetsConnection
from datetime import date, timedelta
from components.gsheets_components import add_new_record

challenge_table_name = "challenges"
users_table_name = "users"
user_challenge_table_name = "user_challenge"

# initialization of dataframes
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet=challenge_table_name, usecols=list(range(8)))
challenges_df = data.dropna(subset=["challenge_id"])

data = conn.read(worksheet=users_table_name, usecols=list(range(5)))
user_df = data.dropna(subset=["user_id"])

user_challenge_df = conn.read(worksheet=user_challenge_table_name)

# initialize session variables
if "task_description" not in st.session_state:
    st.session_state.task_description = ""
    st.session_state.task_award = ""
    st.session_state.task_planned_time = ""


# rewrite values into
def update_table():
    st.session_state.task_description = st.session_state.task_disc_widget
    st.session_state.task_award = st.session_state.task_award_widget
    st.session_state.task_planned_time = st.session_state.task_planned_time_widget

    # clean text fields
    st.session_state.task_disc_widget = None
    st.session_state.task_award_widget = None
    st.session_state.task_planned_time_widget = None


with st.sidebar:
    selected = option_menu("M8Agensy", ["Сотрудники", "Задачи", "Награды", "Аналитика"],
                           icons=['house', "list-task", "award"], menu_icon="cast", default_index=0)
if selected == "Сотрудники":
    st.subheader("Редактор сотрудников")
    st.info("Назначение задач сотрудникам")
    users_list = user_df['user_name'].tolist()
    challenges_list = challenges_df['challenge_description'].tolist()
    col1, col2 = st.columns(2)
    with col1:
        selected_user = st.selectbox(label="Cотрудник", index=None, placeholder='Выберите сотрудника',
                                     options=users_list)
        submit_challenges = st.button(label="Назначить")
    with col2:
        selected_challenges = st.multiselect(label="Челленджи", placeholder="Выберите задачи", options=challenges_list)

    if selected_user:
        user_id = user_df[user_df["user_name"] == selected_user]["user_id"].values[0]
        with st.expander(label="Актаульные челленджи",expanded=True):
            actual_user_challenges = user_challenge_df[
                (user_challenge_df["user_id"] == user_id) & (user_challenge_df["challenge_status"] == "New")]
            if actual_user_challenges.shape[0] > 0:
                st.dataframe(actual_user_challenges[
                                 ["challenge_descripion", "assigning_date", "planned_finish_date", "challenge_status"]],
                             column_config={
                                 "challenge_descripion": "Челлендж",
                                 "assigning_date": st.column_config.DateColumn(label="Дата назначения",
                                                                               format="DD.MM.YYYY"),
                                 "planned_finish_date": st.column_config.DateColumn(label="Дата планируемого завершения",
                                                                                    format="DD.MM.YYYY")
                             },
                             hide_index=True)
            else:
                st.info("Упс, похоже, что нет таких задач")

        with st.expander(label="Зевершенные челленджи", expanded=False):
            past_user_challenges = user_challenge_df[
                (user_challenge_df["user_id"] == user_id) & (user_challenge_df["challenge_status"] != "New")]
            if past_user_challenges.shape[0] > 0:
                st.dataframe(past_user_challenges[
                                 ["challenge_descripion", "assigning_date", "planned_finish_date",
                                  "user_challenge_fact_finish_date", "challenge_success"]],
                             column_config={
                                 "challenge_descripion": "Челлендж",
                                 "assigning_date": st.column_config.DateColumn(label="Дата назначения",
                                                                               format="DD.MM.YYYY"),
                                 "planned_finish_date": st.column_config.DateColumn(
                                     label="Дата планируемого завершения",
                                     format="DD.MM.YYYY")
                             },
                             hide_index=True)
            else:
                st.info("Упс, похоже, что нет таких задач")

        if submit_challenges:
            challenges_to_add = []
            for challenge in selected_challenges:
                challenge_id = \
                challenges_df[challenges_df['challenge_description'] == challenge]['challenge_id'].values[0]
                challenge_timing = challenges_df[challenges_df['challenge_description'] == challenge][
                    'challenge_planned_time_completion'].values[0]
                challenges_to_add.append({
                    'user_challenge_id': None,
                    "user_id": user_id,
                    "user_name": selected_user,
                    "challenge_id": challenge_id,
                    "challenge_descripion": challenge,
                    "assigning_date": date.today(),
                    "planned_finish_date": date.today() + timedelta(days=challenge_timing),
                    "user_challenge_fact_finish_date": None,
                    "challenge_status": "New",
                    "challenge_success": "Unknown"
                })
            add_new_record(table_name=user_challenge_table_name,
                           values_to_add=challenges_to_add)

elif selected == "Задачи":
    st.subheader("Редактор задач")
    st.info("Добавление/удаление задач в базе данных")
    col1, col2 = st.columns(2)
    new_task = dict()
    new_task_df = pd.DataFrame()
    with col1:
        st.text_area(label="Задача", key="task_disc_widget",
                     placeholder="Опишите детально задачу",
                     max_chars=200, height=180)
    with col2:
        st.number_input(label="Награда за выполнение",
                        key="task_award_widget",
                        min_value=0, value=None, step=1,
                        placeholder="Введте колличество баллов")
        st.number_input(label="Время на выполнение",
                        key="task_planned_time_widget",
                        min_value=0, value=None, step=1,
                        placeholder="Введите количестов дней...")
        add_new_task = st.button(label="Добавить задачу в базу", on_click=update_table)
    if add_new_task:
        new_task_active = True
        new_task_date_creation = date.today()
        new_task_id = challenges_df["challenge_id"].max() + 1
        new_task = {
            "challenge_id": new_task_id,
            "challenge_description": st.session_state.task_description,
            "challenge_award": st.session_state.task_award,
            "challenge_planned_time_completion": st.session_state.task_planned_time,
            "challenge_active": new_task_active,
            "challenge_date_creation": new_task_date_creation
        }
        new_task_df = pd.DataFrame([new_task])
        df = pd.concat([challenges_df, new_task_df], ignore_index=True)
        df = conn.update(worksheet=challenge_table_name, data=df)
        st.cache_data.clear()
        st.experimental_rerun()

    with st.expander(label="База челленждей"):
        st.dataframe(challenges_df, use_container_width=True,
                     column_config={
                         "task_id": "ID",
                         "task_description": "Описание задачи",
                         "task_award": st.column_config.NumberColumn(label="Награда",
                                                                     help="Баллы за выполение задачи",
                                                                     format="%d"),
                         "task_planned_time_completion": st.column_config.NumberColumn(label="Время на выполнение",
                                                                                       help="Количество дней, отведенное на выполнение задачи",
                                                                                       format="%d"),
                         "task_active": st.column_config.CheckboxColumn(label="Задача в списке?",
                                                                        help="Здесь можно задачу сделать доступной к использованию для выбора",
                                                                        default=False
                                                                        ),
                         "task_date_creation": st.column_config.DateColumn(label="Дата создания",
                                                                           help="Дата, когда задача была создана в системе",
                                                                           format="DD.MM.YYYY"),
                         "task_last_update": st.column_config.DateColumn(label="Дата обновления",
                                                                         help="Дата, когда задача была обновлена последний раз",
                                                                         format="DD.MM.YYYY")
                     },
                     hide_index=True
                     )
elif selected == "Награды":
    st.subheader("Редактор наград")
    st.info("Добавление/удаление задач в базе данных")
elif selected == "Аналитика":
    st.subheader("Раздел аналитики по сотрудникам")
    st.info("Визуализация статистики по сотрудникам")
