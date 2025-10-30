import os
import json
import requests
from datetime import datetime, timedelta

from .constants import *

WS_TOKEN_DIR = "./Token"
WS_TOKEN_PATH = WS_TOKEN_DIR + "/KIS_WS_TOKEN.txt"

# 환경변수로부터 API 키와 계좌 정보를 가져옴
APP_KEY = os.environ.get("KIS_APP")
SEC_KEY = os.environ.get("KIS_SEC")

# 메모리상에 웹소켓 토큰을 유지하기 위한 딕셔너리
ws_token_dict = {

}

def get_ws_token():
    global ws_token_dict

    json_token = {}
    approval_key = ""

    # 메모리 상의 웹소켓 토큰의 유효 기간을 검사
    if 'ws_token_token_expired' in ws_token_dict:
        token_time = datetime.strptime(ws_token_dict['ws_token_token_expired'], '%Y-%m-%d %H:%M:%S')
        now = datetime.now()

        if now < token_time:
            #print('Current token in memory is available. Return it.')
            approval_key = ws_token_dict['approval_key']
            return approval_key

    # 토큰 디렉터리가 존재하지 않으면 토큰 디렉터리 생성
    if not os.path.exists(WS_TOKEN_DIR):
        os.makedirs(WS_TOKEN_DIR, exist_ok=True)
    
    # 파일로 저장된 웹소켓 토큰의 유효 기간을 검사
    try:
        with open(WS_TOKEN_PATH, 'r', encoding='utf-8') as f:
            json_token = json.load(f)

            token_time = datetime.strptime(json_token['ws_token_token_expired'], '%Y-%m-%d %H:%M:%S')
            now = datetime.now()

            if now < token_time:
                print('Current token in file is available. Return it.')
                ws_token_dict = json_token
                approval_key = ws_token_dict['approval_key']
                return approval_key
    except FileNotFoundError:
        print(f'Failed to open file: {WS_TOKEN_PATH} for reading.')

    # KIS API 서버에 새로운 웹소켓 토큰을 요청
    print('Current token in file is expired. Request new token.')
    json_req = {
        'grant_type': 'client_credentials',
        'appkey': APP_KEY,
        'secretkey': SEC_KEY,
    }
    headers = { 'content-type': 'application/json' }
    resp = requests.post(API_URL + '/oauth2/Approval', headers=headers, data=json.dumps(json_req))

    if 'approval_key' in resp.json():
        print(resp.text)
        approval_key = resp.json()['approval_key']
        try:
            with open(WS_TOKEN_PATH, 'w', encoding='utf-8') as file:
                # 만료 시간 지정
                json_token = resp.json()
                expired_time = datetime.now() + timedelta(hours=24)
                json_token['ws_token_token_expired'] = expired_time.strftime('%Y-%m-%d %H:%M:%S')
                ws_token_dict = json_token
                json.dump(json_token, file, ensure_ascii=False, indent=4)
        except FileNotFoundError:
            print(f'Failed to open file: {WS_TOKEN_PATH} for writing.')
    else:
        print('Invalid Response:')
        print(resp.text)
    
    return approval_key