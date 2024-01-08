import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Admin Page", page_icon="📈", layout="wide")


conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet="tasks", usecols=list(range(8)), max_entries=5)
df = data.dropna(subset=["task_id"])
# 1. as sidebar menu
with st.sidebar:
    selected = option_menu("M8Agensy", ["Сотрудники", "Задачи", "Награды", "Аналитика"],
                           icons=['house', "list-task", "award"], menu_icon="cast", default_index=0)
if selected=="Сотрудники":
    st.subheader("Редактор сотрудников")
    st.info("Назначение задач сотрудникам")
elif selected=="Задачи":
    st.subheader("Редактор задач")
    st.info("Добавление/удаление задач в базе данных")
    with st.expander(label="Существующие задачи", expanded=True):
        st.dataframe(df, use_container_width=True,
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
                                                                             format="DD.MM.YYYY")
                       },
                       hide_index=True
                       )
    with st.expander(label="Добавить новую задачу", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.text_area(label="Задача", placeholder="Опишите детально задачу", max_chars = 200, height=180)
        with col2:
            st.number_input(label="Награда за выполнение",
                            min_value =0, value=0, step=1,
                            placeholder="Введте колличество баллов")
            st.number_input(label="Время на выполнение",
                            min_value =0, value=0, step=1,
                            placeholder="Введите количестов дней...")
            st.button(label="Добавить задачу в базу")
elif selected=="Награды":
    st.subheader("Редактор наград")
    st.info("Добавление/удаление задач в базе данных")
elif selected == "Аналитика":
    st.subheader("Раздел аналитики по сотрудникам")
    st.info("Визуализация статистики по сотрудникам")