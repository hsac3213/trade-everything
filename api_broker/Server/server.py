from ..BrokerCommon.BrokerFactory import BrokerFactory
from ..Common.TokenManager import TokenManager
from .auth_dependency import get_current_user, get_user_from_token
from ..Common.Debug import *
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pprint import pprint

#from ..Binance.BinanceBroker import *
#from ..KIS.KISBroker import *
from ..KIS.token_manager import get_key

# 라우터 import
from .auth import router as auth_router
from .user_settings_router import router as user_settings_router
from .api_key_router import router as api_key_router

SERVER_NAME = "Trade Everything API Broker Server"
SERVER_PORT = 8001

app = FastAPI(title=SERVER_NAME)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    # React/Vite 개발 서버
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://192.168.0.21:5173",
        "http://10.34.78.8:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)
app.include_router(user_settings_router)
app.include_router(api_key_router)

@app.websocket("/ws/order_update/{broker_name}")
async def websocket_order_update(ws: WebSocket, broker_name: str):
    """
    실시간 주문 업데이트 구독
    -> 주문 접수/체결/취소 등
    """
    await ws.accept()
    
    broker = None
    subscription_task = None
    is_connected = True
    
    try:
        auth_message = await asyncio.wait_for(
            ws.receive_json(),
            timeout=10.0
        )
        
        token = auth_message.get("token")
        if not token:
            await ws.send_json({
                "type": "error",
                "message": "Token is required."
            })
            await ws.close(code=1008)
            return
        
        # 클라이언트 정보 추출 (핑거프린트 검증용)
        client_ip = ws.client.host if ws.client else "unknown"
        user_agent = ws.headers.get("user-agent", "")
        
        # 사용자 인증 (핑거프린트 검증 포함)
        try:
            user = await get_user_from_token(token, client_ip, user_agent)
        except Exception as e:
            await ws.send_json({
                "type": "error",
                "message": "Authentication failed."
            })
            await ws.close(code=1008)
            return
        
        # 인증 성공 알림
        await ws.send_json({
            "type": "authenticated",
            "user_id": user["user_id"]
        })
        
        broker = BrokerFactory.create_broker(broker_name, user["user_id"])
        
        async def send_callback(data: dict):
            nonlocal is_connected
            if not is_connected:
                raise asyncio.CancelledError("Client disconnected")
            try:
                await ws.send_json({
                    "type": "userdata",
                    "data": data
                })
            except WebSocketDisconnect:
                is_connected = False
                raise asyncio.CancelledError("Client disconnected")
            except Exception as e:
                is_connected = False
                raise asyncio.CancelledError(f"Send error: {e}")
        
        subscription_task = asyncio.create_task(
            broker.subscribe_order_update_async(send_callback)
        )
        await subscription_task
    
    except asyncio.TimeoutError:
        Error(f"Authentication timeout: {broker_name}")
        try:
            await ws.send_json({
                "type": "error",
                "message": "Authentication timeout"
            })
        except:
            pass
        try:
            await ws.close(code=1008)
        except:
            pass
    except WebSocketDisconnect:
        is_connected = False
    except asyncio.CancelledError:
        is_connected = False
    except Exception as e:
        is_connected = False
        Error(f"Userdata WebSocket error: {e}")
        try:
            await ws.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        except:
            pass
    finally:
        is_connected = False
        if subscription_task and not subscription_task.done():
            subscription_task.cancel()
            try:
                await subscription_task
            except (asyncio.CancelledError, Exception):
                pass
        Info(f"Userdata closed: {broker_name}")

@app.get("/")
def get_root():
    return {
        "message": "hello",
    }

@app.get("/brokers")
def get_brokers():
    return {
        "message": "success",
        "brokers": BrokerFactory.get_available_brokers()
    }

@app.post("/place_order/{broker_name}")
async def place_order(broker_name: str, order: dict, current_user: dict = Depends(get_current_user)):
    try:
        broker = BrokerFactory.create_broker(broker_name, current_user["user_id"])
        result = broker.place_order(order)

        if result["result"] == "success":
            return {
                "result": "success",
                "broker": broker_name,
            }
        else:
            return {
                "result": "error",
                "message": result["message"],
            }
    except Exception as e:
        return {
            "result": "error",
            "message": str(e)
        }
    
@app.post("/cancel_order/{broker_name}")
async def cancel_order(broker_name: str, order: dict, current_user: dict = Depends(get_current_user)):
    try:
        broker = BrokerFactory.create_broker(broker_name, current_user["user_id"])
        result = broker.cancel_order(order)

        if result["result"] == "success":
            return {
                "message": "success",
                "broker": broker_name,
                "result": result,
            }
        else:
            return {
                "message": "error",
                "error": result["message"],
            }
    except Exception as e:
        return {
            "message": "error",
            "error": str(e)
        }
    
@app.post("/cancel_all_orders/{broker_name}")
async def cancel_all_orders(broker_name: str, current_user: dict = Depends(get_current_user)):
    try:
        broker = BrokerFactory.create_broker(broker_name, current_user["user_id"])
        result = broker.cancel_all_orders()

        if result["result"] == "success":
            return {
                "message": "success",
                "broker": broker_name,
                "result": result,
            }
        else:
            return {
                "message": "error",
                "error": result["message"],
            }
    except Exception as e:
        return {
            "message": "error",
            "error": str(e)
        }

@app.get("/orders/{broker_name}")
async def get_orders(broker_name: str, current_user: dict = Depends(get_current_user)):
    try:
        broker = BrokerFactory.create_broker(broker_name, current_user["user_id"])
        orders = broker.get_orders()
        # Info("") ; print(orders)
        return {
            "message": "success",
            "broker": broker_name,
            "orders": orders,
        }
    except Exception as e:
        return {
            "message": "error",
            "error": str(e)
        }

@app.websocket("/ws/userdata/{broker_name}")
async def websocket_userdata(
    ws: WebSocket,
    broker_name: str,
):
    await ws.accept()
    
    broker = None
    subscription_task = None
    is_connected = True
    
    try:
        # 타임아웃과 함께 인증 메시지 수신
        auth_message = await asyncio.wait_for(
            ws.receive_json(),
            timeout=10.0
        )
        
        token = auth_message.get("token")
        if not token:
            await ws.send_json({
                "type": "error",
                "message": "Token is required"
            })
            await ws.close(code=1008)
            return
        
        # 클라이언트 정보 추출 (핑거프린트 검증용)
        client_ip = ws.client.host if ws.client else "unknown"
        user_agent = ws.headers.get("user-agent", "")
        
        # 사용자 인증 (핑거프린트 검증 포함)
        try:
            user = await get_user_from_token(token, client_ip, user_agent)
        except Exception as e:
            await ws.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await ws.close(code=1008)
            return
        
        # 인증 성공 알림
        await ws.send_json({
            "type": "authenticated",
            "user_id": user["user_id"]
        })
        
        broker = BrokerFactory.create_broker(broker_name, user["user_id"])
        
        async def send_callback(data: dict):
            nonlocal is_connected
            if not is_connected:
                raise asyncio.CancelledError("Client disconnected")
            try:
                await ws.send_json({
                    "type": "userdata",
                    "data": data
                })
            except WebSocketDisconnect:
                is_connected = False
                raise asyncio.CancelledError("Client disconnected")
            except Exception as e:
                is_connected = False
                raise asyncio.CancelledError(f"Send error: {e}")
        
        subscription_task = asyncio.create_task(
            broker.subscribe_userdata_async(send_callback)
        )
        await subscription_task
    
    except asyncio.TimeoutError:
        print(f"⏱️ Authentication timeout: {broker_name}")
        try:
            await ws.send_json({
                "type": "error",
                "message": "Authentication timeout"
            })
        except:
            pass
        try:
            await ws.close(code=1008)
        except:
            pass
    except WebSocketDisconnect:
        is_connected = False
    except asyncio.CancelledError:
        is_connected = False
    except Exception as e:
        is_connected = False
        print(f"❌ Userdata WebSocket error: {e}")
        try:
            await ws.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        except:
            pass
    finally:
        is_connected = False
        if subscription_task and not subscription_task.done():
            subscription_task.cancel()
            try:
                await subscription_task
            except (asyncio.CancelledError, Exception):
                pass
        print(f"Userdata closed: {broker_name}")

@app.get("/assets")
def get_assets(current_user: dict = Depends(get_current_user)):
    """
    통합 자산 조회
    """
    try:
        total_assets = []
        for broker_name in BrokerFactory.get_available_brokers():
            broker = BrokerFactory.create_broker(broker_name, current_user["user_id"])
            broker_assets = broker.get_assets()
            for asset in broker_assets:
                asset["broker"] = broker_name
                total_assets.append(asset)
            #total_assets.extend(broker_assets)
        return {
            "message": "success",
            "assets": total_assets
        }
    except Exception as e:
        return {
            "message": "error",
            "error": str(e)
        }

@app.get("/symbols/{broker_name}")
def get_symbols(broker_name: str):
    """브로커의 거래 가능한 심볼 목록 조회"""
    try:
        broker = BrokerFactory.create_broker(broker_name)
        symbols = broker.get_symbols()
        return {
            "message": "success",
            "broker": broker_name,
            "symbols": symbols
        }
    except Exception as e:
        return {
            "message": "error",
            "error": str(e)
        }

@app.get("/candle/{broker_name}")
def get_candle(broker_name: str, symbol: str, interval: str, end_time: str, current_user: dict = Depends(get_current_user)):
    """
    캔들 차트 데이터 조회
    """
    try:
        #print(end_time)
        
        broker = BrokerFactory.create_broker(broker_name, current_user["user_id"])
        candles = broker.get_candle(symbol, interval, end_time)

        return {
            "message": "success",
            "broker": broker_name,
            "candles": candles
        }
    except Exception as e:
        return {
            "message": "error",
            "error": str(e)
        }

@app.websocket("/ws/orderbook/{broker_name}/{symbol}")
async def websocket_orderbook(ws: WebSocket, broker_name: str, symbol: str):
    """
    호가 데이터 구독
    """
    await ws.accept()
    Info(f"[ {broker_name}/{symbol} ]")
    
    broker = None
    subscription_task = None
    is_connected = True
    
    try:
        # 타임아웃과 함께 인증 메시지 수신
        auth_message = await asyncio.wait_for(
            ws.receive_json(),
            timeout=10.0
        )
        
        token = auth_message.get("token")
        if not token:
            await ws.send_json({
                "type": "error",
                "message": "Token is required"
            })
            await ws.close(code=1008)
            return
        
        # 클라이언트 정보 추출 (핑거프린트 검증용)
        client_ip = ws.client.host if ws.client else "unknown"
        user_agent = ws.headers.get("user-agent", "")
        
        # 사용자 인증 (핑거프린트 검증 포함)
        try:
            user = await get_user_from_token(token, client_ip, user_agent)
        except Exception as e:
            await ws.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await ws.close(code=1008)
            return
        
        # 인증 성공 알림
        await ws.send_json({
            "type": "authenticated",
            "user_id": user["user_id"]
        })
        user_id = user["user_id"]
        
        broker = BrokerFactory.create_broker(broker_name, user_id)
        
        async def send_callback(data: dict):
            nonlocal is_connected
            if not is_connected:
                raise asyncio.CancelledError("Client disconnected")
            try:
                if data["symbol"].lower() == symbol.lower():
                    await ws.send_json(data)
                    
            except WebSocketDisconnect:
                is_connected = False
                raise asyncio.CancelledError("Client disconnected")
            except Exception as e:
                is_connected = False
                raise asyncio.CancelledError(f"Send error: {e}")
        
        subscription_task = asyncio.create_task(
            broker.subscribe_orderbook_async(user_id, symbol, send_callback)
        )
        await subscription_task
    
    except asyncio.TimeoutError:
        Error(f"Orderbook authentication timeout: {broker_name}/{symbol}")
        try:
            await ws.send_json({
                "type": "error",
                "message": "Authentication timeout"
            })
        except:
            pass
        try:
            await ws.close(code=1008)
        except:
            pass
    except WebSocketDisconnect:
        is_connected = False
    except asyncio.CancelledError:
        is_connected = False
    except Exception as e:
        is_connected = False
        Error(f"Orderbook WS: {e}")
        try:
            await ws.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        except:
            pass
    finally:
        is_connected = False
        if subscription_task and not subscription_task.done():
            subscription_task.cancel()
            try:
                await subscription_task
            except (asyncio.CancelledError, Exception):
                pass
        Info(f"[ OrderBook WS Closed {broker_name}/{symbol} ]")


@app.websocket("/ws/trade/{broker_name}/{symbol}")
async def websocket_trade(ws: WebSocket, broker_name: str, symbol: str):
    """
    실시간 체결 데이터 구독
    """
    await ws.accept()
    
    broker = None
    subscription_task = None
    is_connected = True
    
    try:
        # 타임아웃과 함께 인증 메시지 수신
        auth_message = await asyncio.wait_for(
            ws.receive_json(),
            timeout=10.0
        )
        
        token = auth_message.get("token")
        if not token:
            await ws.send_json({
                "type": "error",
                "message": "Token is required"
            })
            await ws.close(code=1008)
            return
        
        # 클라이언트 정보 추출 (핑거프린트 검증용)
        client_ip = ws.client.host if ws.client else "unknown"
        user_agent = ws.headers.get("user-agent", "")
        
        # 사용자 인증 (핑거프린트 검증 포함)
        try:
            user = await get_user_from_token(token, client_ip, user_agent)
        except Exception as e:
            await ws.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await ws.close(code=1008)
            return
        
        # 인증 성공 알림
        await ws.send_json({
            "type": "authenticated",
            "user_id": user["user_id"]
        })
        user_id = user["user_id"]
        
        broker = BrokerFactory.create_broker(broker_name, user["user_id"])
        
        async def send_callback(data: dict):
            nonlocal is_connected
            if not is_connected:
                raise asyncio.CancelledError("Client disconnected")
            try:
                if data["symbol"].lower() == symbol.lower():
                    await ws.send_json(data)
            except WebSocketDisconnect:
                is_connected = False
                raise asyncio.CancelledError("Client disconnected")
            except Exception as e:
                is_connected = False
                raise asyncio.CancelledError(f"Send error: {e}")
        
        subscription_task = asyncio.create_task(
            broker.subscribe_trade_price_async(user_id, symbol, send_callback)
        )
        await subscription_task
    
    except asyncio.TimeoutError:
        print(f"⏱️ Trade authentication timeout: {broker_name}/{symbol}")
        try:
            await ws.send_json({
                "type": "error",
                "message": "Authentication timeout"
            })
        except:
            pass
        try:
            await ws.close(code=1008)
        except:
            pass
    except WebSocketDisconnect:
        is_connected = False
    except asyncio.CancelledError:
        is_connected = False
    except Exception as e:
        is_connected = False
        print(f"❌ Trade WebSocket error: {e}")
        try:
            await ws.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        except:
            pass
    finally:
        is_connected = False
        if subscription_task and not subscription_task.done():
            subscription_task.cancel()
            try:
                await subscription_task
            except (asyncio.CancelledError, Exception):
                pass
        print(f"🔌 Trade closed: {broker_name}/{symbol}")

def main():
    Info(f"Starting {SERVER_NAME}...")

    #broker = BinanceBroker("2")
    #broker.get_assets()

    #print(get_key(4))

    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT, log_level="info")
    #uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT, log_level="error")

if __name__ == "__main__":
    main()