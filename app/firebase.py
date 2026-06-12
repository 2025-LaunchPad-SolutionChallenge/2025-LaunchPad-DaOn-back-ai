import json

import firebase_admin
from firebase_admin import credentials

from app.config import settings


def init_firebase() -> None:
    if not firebase_admin._apps:
        if settings.FIREBASE_CREDENTIALS_JSON:
            cred = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS_JSON))
        else:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
