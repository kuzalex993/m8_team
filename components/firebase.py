import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate('./configuration/m8-agency-2e7b37294714.json')
# firebase_admin.initialize_app(cred)
db = firestore.client()


def get_credentials() -> dict():
    doc_ref = db.collection("credentials")
    docs = doc_ref.stream()
    res = dict()
    for doc in docs:
        res[doc.id] = doc.to_dict()
    return res


def add_user(config: dict()) -> dict():
    for key in list(config.keys()):
        try:
            doc_ref = db.collection("credentials").document(key)
            doc_ref.set(config[key])
            print("Success!")
        except Exception as e:
            print(f"{e}")
            # Need to add some tracking of errors
    return True
