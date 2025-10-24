import os
import json
import requests
from datetime import datetime

from constants import *

TOKEN_DIR = "./Token"
TOKEN_PATH = TOKEN_DIR + "/KIS_TOKEN.txt"

# 환경변수로부터 API 키와 계좌 정보를 가져옴
APP_KEY = os.environ.get("KIS_APP")
SEC_KEY = os.environ.get("KIS_SEC")

ACCOUNT_NUMBER_0 = os.environ.get("ACCOUNT_NUMBER_0")
ACCOUNT_NUMBER_1 = os.environ.get("ACCOUNT_NUMBER_1")

# 메모리상에 토큰을 유지하기 위한 딕셔너리
access_token_dict = {

}

def get_access_token():
    global access_token_dict

    json_token = {}
    access_token = ''

    # 메모리 상의 토큰의 유효 기간을 검사
    if 'access_token_token_expired' in access_token_dict:
        token_time = datetime.strptime(access_token_dict['access_token_token_expired'], '%Y-%m-%d %H:%M:%S')
        now = datetime.now()

        if now < token_time:
            #print('Current token in memory is available. Return it.')
            access_token = access_token_dict['access_token']
            return access_token

    # 토큰 디렉터리가 존재하지 않으면 토큰 디렉터리 생성
    if not os.path.exists(TOKEN_DIR):
        os.makedirs(TOKEN_DIR, exist_ok=True)
    
    # 파일로 저장된 토큰의 유효 기간을 검사
    try:
        with open(TOKEN_PATH, 'r', encoding='utf-8') as f:
            json_token = json.load(f)

            token_time = datetime.strptime(json_token['access_token_token_expired'], '%Y-%m-%d %H:%M:%S')
            now = datetime.now()

            if now < token_time:
                print('Current token in file is available. Return it.')
                access_token_dict = json_token
                access_token = access_token_dict['access_token']
                return access_token
    except FileNotFoundError:
        print(f'Failed to open file: {TOKEN_PATH} for reading.')

    # KIS API 서버에 새로운 토큰을 요청
    print('Current token in file is expired. Request new token.')
    json_req = {
        'grant_type': 'client_credentials',
        'appkey': APP_KEY,
        'appsecret': SEC_KEY,
    }
    headers = { 'content-type': 'application/json' }
    resp = requests.post(API_URL + '/oauth2/tokenP', headers=headers, data=json.dumps(json_req))

    if 'access_token' in resp.json():
        access_token = resp.json()['access_token']
        try:
            with open(TOKEN_PATH, 'w', encoding='utf-8') as file:
                json.dump(resp.json(), file, ensure_ascii=False, indent=4)
        except FileNotFoundError:
            print(f'Failed to open file: {TOKEN_PATH} for writing.')
    else:
        print('Invalid Response:')
        print(resp.text)

    access_token_dict = resp.json()
    return access_token