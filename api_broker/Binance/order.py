from .common import API_URL, BINANCE_ED25519_API_KEY
from .common import get_signed_payload_post

import requests
from pprint import pprint

def place_order(user, order):
    try:
        headers = {
            "X-MBX-APIKEY": BINANCE_ED25519_API_KEY,
        }

        params = {
            "symbol": str(order["symbol"]).upper(),
            "side": order["side"],
            "type": "LIMIT",

            "timeInForce": "GTC",
            "price": str(order["price"]),
            "quantity": str(order["quantity"]),
        }
        payload = get_signed_payload_post(params)

        url = API_URL + f"/api/v3/order"
        resp = requests.post(url, headers=headers, data=payload, timeout=10)
        resp_json = resp.json()

        pprint(resp_json)
        
        result = {
            "result": "error",
        }

        if "orderId" in resp_json:
            result["result"] = "success"
            result["order_id"] = "order_id"
            result["order"] = order
        
        if "msg" in resp_json:
            result["message"] = resp_json["msg"]

        return result

    except requests.exceptions.RequestException as e:
        print("[ get_orders ]")
        print("requests.exceptions.RequestException:")
        print(e)
        return []
    except Exception as e:
        print("[ get_orders ]")
        print(e)
        import traceback
        traceback.print_exc()
        return []