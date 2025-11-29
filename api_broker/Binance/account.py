from .common import API_URL, get_key
from .common import get_signed_payload_post
from ..Common.Debug import *

from typing import List, Dict, Any, Callable, Awaitable
import requests
import time

from pprint import pprint

def get_assets(user_id) -> List[Dict[str, Any]]:
    try:
        headers = {
            "X-MBX-APIKEY": get_key(user_id)["API"],
        }

        params = {}
        payload = get_signed_payload_post(user_id, params)

        url = API_URL + f"/sapi/v3/asset/getUserAsset"
        resp = requests.post(url, headers=headers, data=payload, timeout=10)
        resp_json = resp.json()

        assets = []
        for asset in resp_json:
            assets.append({
                "display_name": "Spot " + asset["asset"],
                "symbol": asset["asset"],
                "amount": asset["free"],
            })

        params = {}
        payload = get_signed_payload_post(user_id, params)

        url = API_URL + f"/sapi/v1/simple-earn/account"
        resp = requests.get(url, headers=headers, params=payload, timeout=10)
        resp_json = resp.json()

        assets.append({
            "display_name": "Simple Earn USDT",
            "symbol": "USDT",
            "amount": resp_json["totalAmountInUSDT"],
        })

        return assets
    except requests.exceptions.RequestException as e:
        Error("requests.exceptions.RequestException")
        print(e)
        return []
    except Exception as e:
        Error("Exception")
        print(e)
        return []