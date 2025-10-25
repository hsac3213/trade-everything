from constants import API_URL, APP_KEY, SEC_KEY
import uuid
import jwt
import requests

def get_account_assets():
  payload = {
    "access_key": APP_KEY,
    "nonce": str(uuid.uuid4()),
  }

  jwt_token = jwt.encode(payload, SEC_KEY, algorithm="HS256")

  headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Accept": "application/json",
  }

  resp = requests.get(f"{API_URL}/v1/accounts", headers=headers)
  return resp.json()