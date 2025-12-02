from .constants import API_URL, COLUMN_TO_KOR_DICT, DAY_MARKET_TIME
from .constants import check_market_time
from ..Common.Debug import *
from .token_manager import get_access_token, get_key

import traceback
import requests
from pprint import pprint

def place_order(user_id, order):
    try:
        result = {
            "result": "error",
            "message": "Invalid side.",
        }

        tr_id = ""

        # 매수 주문
        if order["side"] == "buy":
            tr_id = "TTTT1002U"
        # 매도 주문
        elif order["side"] == "sell":
            tr_id = "TTTT1006U"
        else:
            print(order)
            return result

        payload = {
            "CANO": get_key(user_id)["account_number_0"],
            "ACNT_PRDT_CD": get_key(user_id)["account_number_1"],
            "OVRS_EXCG_CD": "NASD",
            "PDNO": str(order["symbol"]).upper(),
            "ORD_QTY": str(order["quantity"]),
            "OVRS_ORD_UNPR": str(order["price"]),
            "ORD_SVR_DVSN_CD": "0",
            # 주문구분
            "ORD_DVSN": "00",
        }

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": "Bearer " + get_access_token(user_id),
            "appkey": get_key(user_id)["app_key"],
            "appsecret": get_key(user_id)["sec_key"],
            "tr_id": tr_id,
            "custtype": "P",
        }

        url = API_URL + f"/uapi/overseas-stock/v1/trading/order"
        resp = requests.post(url, data=payload, headers=headers, timeout=10)
        pprint(resp.text)
        resp_json = resp.json()

        if "ODNO" in resp_json:
            result["result"] = "success"
            result["order_id"] = resp_json["ODNO"]
            result["order"] = order
        
        if "msg" in resp_json:
            result["message"] = resp_json["msg"]

        pprint(result)

        return result
    except requests.exceptions.RequestException as e:
        Error("KIS requests.exceptions.RequestException")
        print(e)
        return {}
    except Exception as e:
        Error("KIS Exception")
        traceback.print_exc()
        return {}
    
def cancel_order(user_id, order):
    try:
        result = {
            "result": "error",
            "message": "",
        }

        # 주간거래 시간 처리
        if check_market_time(DAY_MARKET_TIME):
            payload = {
                "CANO": get_key(user_id)["account_number_0"],
                "ACNT_PRDT_CD": get_key(user_id)["account_number_1"],
                "OVRS_EXCG_CD": "NASD",
                "PDNO": str(order["symbol"]).upper(),
                "ORGN_ODNO": str(order["order_id"]),
                "RVSE_CNCL_DVSN_CD": "02",
                "ORD_QTY": "1",
                "OVRS_ORD_UNPR": "0",
                "CTAC_TLNO": "",
                "MGCO_APTM_ODNO": "",
                "ORD_SVR_DVSN_CD": "0",
            }

            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": "Bearer " + get_access_token(user_id),
                "appkey": get_key(user_id)["app_key"],
                "appsecret": get_key(user_id)["sec_key"],
                "tr_id": "TTTS6038U",
                "custtype": "P",
            }

            url = API_URL + f"/uapi/overseas-stock/v1/trading/daytime-order-rvsecncl"
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp_json = resp.json()

            Info(resp_json)

            if "ODNO" in resp_json:
                result["result"] = "success"
                result["order_id"] = resp_json["ODNO"]
                result["order"] = order
            
            if "msg" in resp_json:
                result["message"] = resp_json["msg"]

            return result
        
        # 메인 마켓 처리
        else:
            result = {
                "result": "error",
                "message": "",
            }

            payload = {
                "CANO": get_key(user_id)["account_number_0"],
                "ACNT_PRDT_CD": get_key(user_id)["account_number_1"],
                "OVRS_EXCG_CD": "NASD",
                "PDNO": str(order["symbol"]).upper(),
                "ORGN_ODNO": str(order["order_id"]),
                "RVSE_CNCL_DVSN_CD": "02",
                "ORD_QTY": "1",
                "OVRS_ORD_UNPR": "0",
                "MGCO_APTM_ODNO": "",
                "ORD_SVR_DVSN_CD": "0",
            }

            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": "Bearer " + get_access_token(user_id),
                "appkey": get_key(user_id)["app_key"],
                "appsecret": get_key(user_id)["sec_key"],
                "tr_id": "TTTT1004U",
                "custtype": "P",
            }

            url = API_URL + f"/uapi/overseas-stock/v1/trading/order-rvsecncl"
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp_json = resp.json()

            if "ODNO" in resp_json:
                result["result"] = "success"
                result["order_id"] = resp_json["ODNO"]
                result["order"] = order
            
            if "msg" in resp_json:
                result["message"] = resp_json["msg"]

            #pprint(result)

            return result
    except requests.exceptions.RequestException as e:
        Error("KIS requests.exceptions.RequestException")
        print(e)
        return {}
    except Exception as e:
        Error("KIS Exception")
        traceback.print_exc()
        return {}