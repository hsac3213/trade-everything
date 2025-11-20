from .common import API_URL, get_signed_payload_post, get_key
from ..Common.Debug import *

import requests
import traceback
from pprint import pprint

def place_order(user_id, order):
    try:
        headers = {
            "X-MBX-APIKEY": get_key(user_id)["API"],
        }

        params = {
            "symbol": str(order["symbol"]).upper(),
            "side": order["side"],
            "type": "LIMIT",

            "timeInForce": "GTC",
            "price": str(order["price"]),
            "quantity": str(order["quantity"]),
        }
        payload = get_signed_payload_post(user_id, params)

        url = API_URL + f"/api/v3/order"
        resp = requests.post(url, headers=headers, data=payload, timeout=10)
        resp_json = resp.json()
        
        result = {
            "result": "error",
            "message": "",
        }

        if "orderId" in resp_json:
            result["result"] = "success"
            result["order_id"] = "order_id"
            result["order"] = order
        
        if "msg" in resp_json:
            result["message"] = resp_json["msg"]

        pprint(result)

        return result

    except requests.exceptions.RequestException as e:
        print(f"[ {func_name()} ]")
        print("requests.exceptions.RequestException:")
        print(e)
        return []
    except Exception as e:
        print(f"[ {func_name()} ]")
        print(e)
        import traceback
        traceback.print_exc()
        return []

def cancel_order(user_id, order):
    try:
        params = {
            "symbol": str(order["symbol"]).upper(),
            "orderId": order["order_id"],
        }

        headers = {
            "X-MBX-APIKEY": get_key(user_id)["API"],
        }

        payload = get_signed_payload_post(user_id, params)

        url = API_URL + f"/api/v3/order"
        resp = requests.delete(url, headers=headers, data=payload, timeout=10)
        resp_json = resp.json()

        pprint(resp_json)

        print(f"[ {func_name()} ]")
        
        result = {
            "result": "error",
            "message": "",
        }

        if "status" in resp_json:
            if resp_json["status"] == "CANCELED":
                result["result"] = "success"
        
        if "msg" in resp_json:
            result["message"] = resp_json["msg"]

        return result

    except requests.exceptions.RequestException as e:
        print(f"[ {func_name()} ]")
        print("requests.exceptions.RequestException:")
        print(e)
        return []
    except Exception as e:
        print(f"[ {func_name()} ]")
        print(e)
        traceback.print_exc()
        return []
    
def cancel_all_orders(user_id, order):
    try:
        headers = {
            "X-MBX-APIKEY": get_key(user_id)["API"],
        }

        params = {
            "symbol": str(order["symbol"]).upper(),
        }
        payload = get_signed_payload_post(user_id, params)

        url = API_URL + f"/api/v3/openOrders"
        resp = requests.delete(url, headers=headers, data=payload, timeout=10)
        resp_json = resp.json()

        pprint(resp_json)
        
        result = {
            "result": "error",
            "message": "",
        }

        return result

    except requests.exceptions.RequestException as e:
        print(f"[ {func_name()} ]")
        print("requests.exceptions.RequestException:")
        print(e)
        return []
    except Exception as e:
        print(f"[ {func_name()} ]")
        print(e)
        traceback.print_exc()
        return []