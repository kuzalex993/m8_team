from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.base_query import BaseCompositeFilter
from datetime import datetime, date, timedelta
try:
    app = firebase_admin.get_app("firebase_connector")
except ValueError:
    cred = credentials.Certificate('./configuration/m8-agency-2e7b37294714.json')
    app = firebase_admin.initialize_app(cred, name="firebase_connector")

db = firestore.client(app)


def get_credentials() -> dict:
    print("Getting credentials")
    doc_ref = db.collection("credentials")
    docs = doc_ref.stream()
    res = dict()
    for doc in docs:
        res[doc.id] = doc.to_dict()
    return res


def register_user(config: dict) -> bool:
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

def get_collection(collection_name: str):
    print(f"Retrieve {collection_name} data")
    doc_ref = db.collection(collection_name)
    docs = doc_ref.stream()
    items = list(map(lambda x: {**x.to_dict(), 'id': x.id}, docs))
    return items

def get_document(collection_name: str, document_name: str) -> dict:
    print(f"Retrieving data: collection - {collection_name}, document - {document_name}")
    try:
        doc_ref = db.collection(collection_name).document(document_name)
        doc = doc_ref.get()
        doc_data = doc.to_dict()
        return doc_data
    except Exception as e:
        print(e)
        return False

def get_value(collection_name: str, document_name: str, field_name: str):
    try:
        doc_ref = db.collection(collection_name).document(document_name)
        doc = doc_ref.get()
        doc_data = doc.to_dict()
        field_value = doc_data[field_name]
        return field_value
    except Exception as e:
        print(e)
        return False

def add_new_document(collection_name: str, document_data: dict) -> bool:
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
    
def put_into_user_bonus_collection(user_id: int, transaction_type: str, bonus_value: int, event_type: str, event_id: int):
    new_record = {
        "user_id": user_id,
        "transaction_type": transaction_type,
        "bonus_value": bonus_value,
        "event_type": event_type,
        "event_id":event_id,
        "date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }
    if add_new_document("user_bonus", new_record):
        return True
    else:
        False
def put_into_user_challenge_collection(user_id: int, user_name: str, challenge_id: int, 
                                       challenge_descripion: str, start_date: date, challenge_duration: int,
                                       challenge_creation_date: datetime
                                       ):
    new_record = {
        "user_id": user_id,
        "user_name": user_name,
        "challenge_id": challenge_id,
        "challenge_descripion": challenge_descripion,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "planned_finish_date": (start_date+ timedelta(days=challenge_duration)).strftime("%Y-%m-%d"),
        "fact_finish_date": None,
        "challenge_status": "new",
        "challenge_success": "uknonwn",
        "challenge_creation_date": challenge_creation_date
    }
    if add_new_document("user_challenge", new_record):
        return True
    else:
        False

def get_user_challenges(user_id: str, challenge_status: str):

    print(f"Retrieving challenges of {user_id}")
    try:
        filter_list = [FieldFilter("user_id", "==", user_id),FieldFilter("challenge_status", "==", challenge_status)]
        docs = db.collection("user_challenge").where(filter=BaseCompositeFilter("AND",filter_list)).stream()
        return docs
    except Exception as e:
        print(e)
        return False
    
def get_user_rewards(user_id: str):
    print(f"Retrieving rewards of {user_id}")
    if user_id != "all":
        try:
            filter_list = [FieldFilter("user_id", "==", user_id)]
            docs = db.collection("user_reward").where(filter=BaseCompositeFilter("AND",filter_list)).stream()
            return docs
        except Exception as e:
            print(e)
            return False
    else:
        try:
            docs = db.collection("user_reward").stream()
            return docs
        except Exception as e:
            print(e)
            return False