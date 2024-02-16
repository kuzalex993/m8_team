import streamlit as st
st.set_page_config(page_title="My performance", layout="wide", initial_sidebar_state="auto")
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from components.adminPage import show_admin_page
from components.userPage import show_user_page



with open('configuration/users.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login(location='main',
                                                            fields={'Form name': 'Войти в аккаунт',
                                                                    'Username': 'Имя пользователя',
                                                                    'Password': 'Пароль',
                                                                    'Login': 'Войти'})
if  authentication_status == False:
    st.error('Имя пользователя и/или пароль введены неверно')
elif authentication_status is None:
    st.warning('Введите имя пользователя и пароль')
elif authentication_status == True:
    if username == 'jsmith':
        with st.sidebar:
            st.write(f'Welcome *{name}*')
        show_admin_page()
    elif username == 'rbriggs':
        with st.sidebar:
            st.write(f'Welcome *{name}*')
        show_user_page()
    authenticator.logout(button_name='Выйти',
                         location='sidebar')

