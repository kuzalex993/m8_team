"""Firestore access layer. The only place ``firebase_admin`` / ``google.cloud.firestore``
is imported. Repositories return domain models or plain dicts; they never import
``streamlit`` or ``m8_team.backend.services``.
"""
