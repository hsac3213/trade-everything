from .constants import API_URL
from .token_manager import get_access_token, get_key
from ..Common.Debug import *

from typing import List, Dict, Any, Callable, Awaitable
import requests

from pprint import pprint

def get_assets(user_id) -> List[Dict[str, Any]]:
    try:
        # 해외 주식 체결 잔고
        params = {
            "CANO": get_key(user_id)["account_number_0"],
            "ACNT_PRDT_CD": get_key(user_id)["account_number_1"],
            "OVRS_EXCG_CD": "NASD",
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        }

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": "Bearer " + get_access_token(user_id),
            "appkey": get_key(user_id)["app_key"],
            "appsecret": get_key(user_id)["sec_key"],
            "tr_id": "TTTS3012R",
            "custtype": "P",
        }

        url = API_URL + f"/uapi/overseas-stock/v1/trading/inquire-balance"
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp_json = resp.json()

        assets = []
        for asset in resp_json["output1"]:
            assets.append({
                "type": "stock",
                "display_name": asset["ovrs_item_name"],
                "symbol": asset["ovrs_pdno"],
                "amount": asset["ovrs_cblc_qty"],
            })

        # 외화 예수금
        params = {
            "CANO": get_key(user_id)["account_number_0"],
            "ACNT_PRDT_CD": get_key(user_id)["account_number_1"],
        }

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": "Bearer " + get_access_token(user_id),
            "appkey": get_key(user_id)["app_key"],
            "appsecret": get_key(user_id)["sec_key"],
            "tr_id": "TTTC2101R",
            "custtype": "P",
        }

        url = API_URL + f"/uapi/overseas-stock/v1/trading/foreign-margin"
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp_json = resp.json()

        pprint(resp_json)

        for asset in resp_json["output"]:
            if float(asset["frcr_dncl_amt1"]) > 0.0 and asset["natn_name"] == "미국":
                assets.append({
                    "type": "deposit",
                    "display_name": asset["crcy_cd"],
                    "symbol": asset["crcy_cd"],
                    "amount": asset["frcr_dncl_amt1"],
                })

        pprint(assets)

        return assets
    except requests.exceptions.RequestException as e:
        Error("requests.exceptions.RequestException")
        print(e)
        return []
    except Exception as e:
        Error("Exception")
        print(e)
        return []