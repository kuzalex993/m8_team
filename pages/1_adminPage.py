import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_gsheets import GSheetsConnection
from datetime import date, timedelta
from components.gsheets_components import add_new_record, update_table_in_db

challenge_table_name = "challenges"
users_table_name = "users"
rewards_table_name = "rewards"
user_challenge_table_name = "user_challenge"

# initialization of dataframes
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet=challenge_table_name, usecols=list(range(8)))
challenges_df = data.dropna(subset=["challenge_id"])

data = conn.read(worksheet=users_table_name, usecols=list(range(5)))
user_df = data.dropna(subset=["user_id"])

data = conn.read(worksheet=rewards_table_name, usecols=list(range(5)))
rewards_df = data.dropna(subset=["reward_id"])

user_challenge_df = conn.read(worksheet=user_challenge_table_name)

# initialize session variables
if "task_description" not in st.session_state:
    st.session_state.task_description = ""
    st.session_state.task_award = ""
    st.session_state.task_planned_time = ""
if "reward_name" not in st.session_state:
    st.session_state.reward_name = ""
    st.session_state.reward_price = ""


def update_table_create_new_reward():
    st.session_state.reward_name = st.session_state.reward_name_widget
    st.session_state.reward_price = st.session_state.reward_price_widget

    st.session_state.reward_name_widget = None
    st.session_state.reward_price_widget = None


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


with st.sidebar:
    selected = option_menu("M8Agenсy", ["Сотрудники", "Задания", "Награды", "Аналитика"],
                           icons=['house', "list-task", "award"], menu_icon="cast", default_index=0)
if selected == "Сотрудники":
    st.subheader("Редактор сотрудников")
    st.info("Назначение заданий сотрудникам")
    users_list = user_df['user_name'].tolist()
    challenges_list = challenges_df['challenge_description'].tolist()
    col1, col2 = st.columns(2)
    with col1:
        selected_user = st.selectbox(label="Cотрудник", index=None, placeholder='Выберите сотрудника',
                                     options=users_list)
        submit_challenges = st.button(label="Назначить")
    with col2:
        selected_challenges = st.multiselect(label="Задания", placeholder="Выберите задания", options=challenges_list)

    if selected_user:
        user_id = user_df[user_df["user_name"] == selected_user]["user_id"].values[0]
        with st.expander(label="Актаульные задания", expanded=True):
            actual_user_challenges = user_challenge_df[
                (user_challenge_df["user_id"] == user_id) & (user_challenge_df["challenge_status"] == "New")]
            if actual_user_challenges.shape[0] > 0:
                st.dataframe(actual_user_challenges[
                                 ["challenge_descripion", "assigning_date", "planned_finish_date", "challenge_status"]],
                             column_config={
                                 "challenge_descripion": "Задание",
                                 "assigning_date": st.column_config.DateColumn(label="Дата назначения",
                                                                               format="DD.MM.YYYY"),
                                 "planned_finish_date": st.column_config.DateColumn(
                                     label="Дата планируемого завершения",
                                     format="DD.MM.YYYY")
                             },
                             hide_index=True)
            else:
                st.info("Упс, похоже, что нет таких заданий")

        with st.expander(label="Зевершенные задания", expanded=False):
            past_user_challenges = user_challenge_df[
                (user_challenge_df["user_id"] == user_id) & (user_challenge_df["challenge_status"] != "New")]
            if past_user_challenges.shape[0] > 0:
                st.dataframe(past_user_challenges[
                                 ["challenge_descripion", "assigning_date", "planned_finish_date",
                                  "user_challenge_fact_finish_date", "challenge_success"]],
                             column_config={
                                 "challenge_descripion": "Задания",
                                 "assigning_date": st.column_config.DateColumn(label="Дата назначения",
                                                                               format="DD.MM.YYYY"),
                                 "planned_finish_date": st.column_config.DateColumn(
                                     label="Дата планируемого завершения",
                                     format="DD.MM.YYYY")
                             },
                             hide_index=True)
            else:
                st.info("Упс, похоже, что нет таких заданий")

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

elif selected == "Задания":
    st.subheader("Управление заданиями")
    challenges_list = challenges_df['challenge_description'].tolist()
    with st.expander(label="Добавление заданий в базу данных :new:", expanded=True):
        col1, col2 = st.columns(2)
        new_task = dict()
        new_task_df = pd.DataFrame()
        with col1:
            st.text_area(label="Задания", key="task_disc_widget",
                         placeholder="Сформулируйте задание",
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
            add_new_task = st.button(label="Добавить задание в базу", on_click=update_table_create_new_challenge)
        if add_new_task:
            new_task_active = True
            new_task_date_creation = date.today()
            new_task_id = challenges_df["challenge_id"].max() + 1
            new_task = {
                "challenge_id": new_task_id,
                "challenge_description": st.session_state.task_description,
                "challenge_reward": st.session_state.task_award,
                "challenge_planned_time_completion": st.session_state.task_planned_time,
                "challenge_active": new_task_active,
                "challenge_date_update": new_task_date_creation
            }
            new_task_df = pd.DataFrame([new_task])
            df = pd.concat([challenges_df, new_task_df], ignore_index=True)
            df = conn.update(worksheet=challenge_table_name, data=df)
            st.cache_data.clear()
            st.experimental_rerun()
    with st.expander(label="Редактирование задания :pencil2:"):
        col1, col2 = st.columns(2)
        with col1:
            task_to_edit = st.selectbox(label="Задание", placeholder="Выберите задание для изменения",
                                        options=challenges_list, index=None)
            if task_to_edit is None:
                task_disc_to_edit = ""
                task_award_to_edit = None
                task_planned_time_to_edit = None
            else:
                challenge_id = \
                challenges_df[challenges_df["challenge_description"] == task_to_edit]["challenge_id"].values[0]
                selcted_challenge = challenges_df.loc[challenges_df["challenge_id"] == challenge_id]
                task_disc_to_edit = selcted_challenge["challenge_description"].values[0]
                task_award_to_edit = int(selcted_challenge["challenge_reward"].values[0])
                task_planned_time_to_edit = int(selcted_challenge["challenge_planned_time_completion"].values[0])
            st.text_area(value=task_disc_to_edit,
                         label="Задание",
                         key="edit_challenge_disc_widget",
                         placeholder="Название задания",
                         max_chars=200, height=80)
        with col2:
            st.number_input(value=task_award_to_edit,
                            label="Награда за выполнение",
                            key="edit_challenge_reward_widget",
                            min_value=0, step=1,
                            placeholder="Введте колличество баллов")
            st.number_input(value=task_planned_time_to_edit,
                            label="Время на выполнение",
                            key="edit_challenge_planned_time_widget",
                            min_value=0, step=1,
                            placeholder="Введите количестов дней...")
            update_task = st.button(label="Применить изменения", on_click=update_table_update_challenge)
            if update_task:
                challenges_df.loc[
                    challenges_df["challenge_id"] == challenge_id, ["challenge_description",
                                                                    "challenge_reward",
                                                                    "challenge_planned_time_completion",
                                                                    "challenge_date_update"]] = [
                    st.session_state.task_description,
                    st.session_state.task_award,
                    st.session_state.task_planned_time,
                    date.today()]
                update_table_in_db(table_name=challenge_table_name,
                                   df=challenges_df)
        st.divider()
    with st.expander(label="База заданий :books:"):
        st.dataframe(challenges_df, use_container_width=True,
                     column_config={
                         "task_id": "ID",
                         "task_description": "Описание задания",
                         "task_award": st.column_config.NumberColumn(label="Награда",
                                                                     help="Баллы за выполение задания",
                                                                     format="%d"),
                         "task_planned_time_completion": st.column_config.NumberColumn(label="Время на выполнение",
                                                                                       help="Количество дней, отведенное на выполнение задания",
                                                                                       format="%d"),
                         "task_active": st.column_config.CheckboxColumn(label="Задание в списке?",
                                                                        help="Здесь можно задание сделать доступным для выбора",
                                                                        default=False
                                                                        ),
                         "task_date_creation": st.column_config.DateColumn(label="Дата создания",
                                                                           help="Дата, когда задание было создано в системе",
                                                                           format="DD.MM.YYYY"),
                         "task_last_update": st.column_config.DateColumn(label="Дата обновления",
                                                                         help="Дата, когда задание было обновлено последний раз",
                                                                         format="DD.MM.YYYY")
                     },
                     hide_index=True
                     )
elif selected == "Награды":
    st.subheader("Управление наградами")

    rewards_list = rewards_df['reward_name'].tolist()
    with st.expander(label="Добавление наград в базу :new:", expanded=True):
        col1, col2 = st.columns(2)
        new_task = dict()
        new_reward_df = pd.DataFrame()
        with col1:
            st.text_area(label="Название награды", key="reward_name_widget",
                         placeholder="Напишите название награды",
                         max_chars=200)
        with col2:
            st.number_input(label="Стоимость награды",
                            key="reward_price_widget",
                            min_value=0, value=None, step=1,
                            placeholder="Введте колличество баллов")
            add_new_reward = st.button(label="Добавить награду в базу", on_click=update_table_create_new_reward)
        if add_new_reward:
            new_reward_active = True
            new_reward_id = rewards_df["reward_id"].max() + 1
            new_reward = {
                "reward_id": new_reward_id,
                "reward_name": st.session_state.reward_name,
                "reward_discription": None,
                "reward_price": st.session_state.reward_price,
                "reward_status": True
            }
            new_reward_df = pd.DataFrame([new_reward])
            df = pd.concat([rewards_df, new_reward_df], ignore_index=True)
            df = conn.update(worksheet=rewards_table_name, data=df)
            st.cache_data.clear()
            st.experimental_rerun()

    with st.expander(label="База наград"):
        st.dataframe(rewards_df,
                     column_config={
                         "reward_id": "ID",
                         "reward_name": "Награда",
                         "reward_discription": "Детали",
                         "reward_price": "Стоимость награды",
                         "reward_status": "Доступность награды"
                     },
                     hide_index=True
                     )

elif selected == "Аналитика":
    st.subheader("Раздел аналитики по сотрудникам")
    st.info("Визуализация статистики по сотрудникам")
