import os
import json
import requests
from datetime import datetime, timedelta

from constants import *

TOKEN_DIR = "./Token"
TOKEN_PATH = TOKEN_DIR + "/LS_TOKEN.txt"

# 환경변수로부터 API 키와 계좌 정보를 가져옴
APP_KEY = os.environ.get("LS_APP")
SEC_KEY = os.environ.get("LS_SEC")

# 메모리상에 토큰을 유지하기 위한 딕셔너리
access_token_dict = {
    
}

def get_access_token():
    global access_token_dict

    json_token = {}
    access_token = ''

    # 메모리 상의 토큰의 유효 기간을 검사
    if 'ls_token_expired' in access_token_dict:
        token_time = datetime.strptime(access_token_dict['ls_token_expired'], '%Y-%m-%d %H:%M:%S')
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

            token_time = datetime.strptime(json_token['ls_token_expired'], '%Y-%m-%d %H:%M:%S')
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
        'appsecretkey': SEC_KEY,
        'scope': 'oob'
    }
    headers = { 'content-type': 'application/x-www-form-urlencoded' }
    resp = requests.post(API_URL + '/oauth2/token', headers=headers, data=json_req)
    print("[ resp ]")
    print(resp.text)

    if 'access_token' in resp.json():
        access_token = resp.json()['access_token']
        try:
            with open(TOKEN_PATH, 'w', encoding='utf-8') as file:
                # 만료 시간 지정
                resp_json = resp.json()
                expired_time = datetime.now() + timedelta(seconds=resp_json["expires_in"] - 60)
                resp_json["ls_token_expired"] = expired_time.strftime('%Y-%m-%d %H:%M:%S')
                access_token_dict = resp.json()
                json.dump(resp_json, file, ensure_ascii=False, indent=4)
        except FileNotFoundError:
            print(f'Failed to open file: {TOKEN_PATH} for writing.')
    else:
        print('Invalid Response:')
        print(resp.text)

    return access_token