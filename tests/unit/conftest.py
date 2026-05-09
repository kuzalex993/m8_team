from unittest.mock import MagicMock, patch

# Block real Firebase initialization when firebase.py is imported during test collection.
# conftest.py module-level code runs before any test module is imported, so these
# patches are active when firebase.py executes its top-level initialization block.
_patches = (
    patch("firebase_admin.get_app", side_effect=ValueError("no app")),
    patch("firebase_admin.credentials.Certificate", return_value=MagicMock()),
    patch("firebase_admin.initialize_app", return_value=MagicMock()),
    patch("firebase_admin.firestore.client", return_value=MagicMock()),
)
for _p in _patches:
    _p.start()
