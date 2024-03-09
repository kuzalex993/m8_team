import streamlit as st

from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials
try:
    app = firebase_admin.get_app("firebase_connector")
except ValueError:
    cred = credentials.Certificate('./configuration/m8-agency-2e7b37294714.json')
    app = firebase_admin.initialize_app(cred, name="firebase_connector")

db = firestore.client(app)


def get_credentials() -> dict():
    doc_ref = db.collection("credentials")
    docs = doc_ref.stream()
    res = dict()
    for doc in docs:
        res[doc.id] = doc.to_dict()
    return res


def register_user(config: dict()) -> bool:
    try:
        for key in config.keys():
            doc_ref = db.collection("credentials").document(key)
            doc_ref.update(config[key])
        return True
    except Exception as e:
        print(f"Error:{e}")
        return False


def create_user(email: str, user: str, name: str) -> bool:
    data = {
        "user_email": email,
        "user_free_bonuses": 0,
        "user_name": name,
        "user_position": "сотрудник",
        "user_reserved_bonuses": 0,
        "user_role": "user"
    }
    try:
        collection_ref = db.collection("users")
        document_ref = collection_ref.document(user)
        document_ref.set(data)
        return True
    except Exception as e:
        print(e)
        return False


def get_users():
    print("Retrieve users data")
    doc_ref = db.collection("users")
    docs = doc_ref.stream()
    res = dict()
    for doc in docs:
        res[doc.id] = doc.to_dict()
    return res


def update_value(collection: str, document: str, field: str, value: any):
    try:
        doc_ref = db.collection(collection).document(document)
        doc_ref.update({field: value})
        return True
    except Exception as e:
        return False

def get_challenges() -> list():
    print("Retrieve challenges data")
    doc_ref = db.collection("challenges")
    docs = doc_ref.stream()
    items = list(map(lambda x: {**x.to_dict(), 'id': x.id}, docs))
    return items

def add_new_document(collection_name: str, document_data: dict()) -> bool:
    try:
        collection_ref = db.collection(collection_name)
        update_time, document_ref = collection_ref.add(document_data=document_data)
        print(f"{update_time} Added new document with id {document_ref.id}")
        return True
    except Exception as e:
        print(e)
        return False

def update_document(collection_name: str, document_id: str, document_data: dict()) -> bool:
    try:
        doc_ref = db.collection(collection_name).document(document_id)
        doc_ref.update(document_data)
        return True
    except Exception as e:
        print(e)
        return False