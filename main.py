import streamlit as st
st.set_page_config(page_title="My performance", layout="wide", initial_sidebar_state="auto")
import streamlit_authenticator as stauth
from components.firebase import get_credentials, register_user, create_user
from components.adminPage import show_admin_page
from components.userPage import show_user_page
from dotenv import load_dotenv
import os
load_dotenv()

if "users_config" not in st.session_state or st.session_state["users_config"] is None:
    st.session_state["users_config"] = get_credentials()
if "bot_endpoint" not in st.session_state:
    st.session_state["bot_endpoint"] = os.getenv("T_BOT_ENDPOINT")
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

authenticator = stauth.Authenticate(
    st.session_state.users_config['credentials'],
    st.session_state.users_config['cookie']['name'],
    st.session_state.users_config['cookie']['key'],
    st.session_state.users_config['cookie']['expiry_days'],
    st.session_state.users_config['preauthorized']
)

st.session_state["user_name"], authentication_status, st.session_state["user_id"] = authenticator.login(location='main',
                                                                                                    fields={'Form name': 'Войти в аккаунт',
                                                                                                            'Username': 'Имя пользователя',
                                                                                                            'Password': 'Пароль',
                                                                                                            'Login': 'Войти'})

if authentication_status == False:
    st.error('Имя пользователя и/или пароль введены неверно')
elif authentication_status is None:
    st.warning('Введите имя пользователя и пароль')

if authentication_status is not True:
   with st.expander(label="Зарегистрироваться"):
        try:
            email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(
                        location="main",
                        preauthorization=False)
            if email_of_registered_user:
                if register_user(config=st.session_state.users_config):
                    if create_user(email=email_of_registered_user, user=username_of_registered_user, name = name_of_registered_user):
                        st.success("Пользователь успешно зарегистрирован")
                    else:
                        st.error("Could not register user")
                else:
                    st.error("Could not register user")
        except Exception as e:
            st.error(e)

if authentication_status is True:
    if st.session_state["user_id"] == 'admin':
        show_admin_page()
    else:
        show_user_page()
    authenticator.logout(button_name='Выйти',
                         location='sidebar')
    




