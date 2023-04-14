import firebase_admin as fb
import firebase_admin.auth as fbauth
import requests
import json

from os import getenv

FB_AUTH_REST_API_SIGN_IN = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FB_AUTH_REST_API_SIGN_UP = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp"

app = fb.initialize_app()

def create_user(email: str, password: str) -> requests.Response:
    auth_request = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    })

    auth_response = requests.post(FB_AUTH_REST_API_SIGN_UP,
                                  params={"key": str(getenv("FIREBASE_WEB_API_KEY"))}, 
                                  data = auth_request)
    
    return auth_response

def authenticate(email: str, password: str) -> requests.Response:
    auth_request = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    })

    auth_response = requests.post(FB_AUTH_REST_API_SIGN_IN,
                                  params={"key": str(getenv("FIREBASE_WEB_API_KEY"))}, 
                                  data = auth_request)
    return auth_response

EMAIL = "jmartiiiiii@gmail.com"
PASSWORD = "testPassword"
user = create_user(EMAIL,PASSWORD)
print(user)
userAutentication = authenticate(EMAIL,PASSWORD)
print("USER",userAutentication.json()['idToken'])

