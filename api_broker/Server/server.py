from ..BrokerCommon.BrokerFactory import BrokerFactory
from ..Common.TokenManager import TokenManager
from .auth_dependency import get_current_user, get_user_from_token
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio

# 라우터 import
from .auth import router as auth_router
from .user_settings_router import router as user_settings_router

SERVER_NAME = "Trade Everything API Broker Server"
SERVER_PORT = 8001

app = FastAPI(title=SERVER_NAME)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)
app.include_router(user_settings_router)

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

@app.get("/test")
async def test(current_user: dict = Depends(get_current_user)):
    token_manager = TokenManager()
    return {
        "user": current_user.get("email"),
        "tokens": token_manager.get_tokens(current_user["user_id"], "Binance")
    }

@app.post("/place_order/{broker_name}")
async def place_order(broker_name: str, order: dict, current_user: dict = Depends(get_current_user)):
    try:
        broker = BrokerFactory.create_broker(broker_name)
        result = broker.place_order(order)

        if result["result"] == "success":
            return {
                "result": "success",
                "broker": broker_name,
                "result": result,
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

@app.get("/orders/{broker_name}")
async def get_orders(broker_name: str, current_user: dict = Depends(get_current_user)):
    try:
        broker = BrokerFactory.create_broker(broker_name)
        orders = broker.get_orders()
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
        auth_message = await ws.receive_json()
        token = auth_message.get("token")
        user = await get_user_from_token(token)
        
        broker = BrokerFactory.create_broker(broker_name)
        
        async def send_callback(data: dict):
            print("[ zzz ]")
            print(data)
            nonlocal is_connected
            if not is_connected:
                raise asyncio.CancelledError("Client disconnected")
            try:
                await ws.send_json(data)
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
    
    except WebSocketDisconnect:
        is_connected = False
    except asyncio.CancelledError:
        is_connected = False
    except Exception as e:
        is_connected = False
        print(f"Userdata WebSocket error: {e}")
    finally:
        is_connected = False
        if subscription_task and not subscription_task.done():
            subscription_task.cancel()
            try:
                await subscription_task
            except (asyncio.CancelledError, Exception):
                pass
        print(f"Userdata closed: {broker_name}")

@app.get("/assets/{broker_name}")
def get_assets(broker_name: str):
    try:
        broker = BrokerFactory.create_broker(broker_name)
        symbols = broker.get_assets()
        return {
            "message": "success",
            "broker": broker_name,
            "assets": symbols
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
def get_candle(broker_name: str, symbol: str, interval: str, start_time: str):
    try:
        print(start_time)
        broker = BrokerFactory.create_broker(broker_name)
        candles = broker.get_candle(symbol, interval, start_time)

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
    await ws.accept()
    print(f"✅ Orderbook connected: {broker_name}/{symbol}")
    
    broker = None
    subscription_task = None
    is_connected = True
    
    try:
        broker = BrokerFactory.create_broker(broker_name)
        
        async def send_callback(data: dict):
            nonlocal is_connected
            if not is_connected:
                raise asyncio.CancelledError("Client disconnected")
            try:
                await ws.send_json(data)
            except WebSocketDisconnect:
                is_connected = False
                raise asyncio.CancelledError("Client disconnected")
            except Exception as e:
                is_connected = False
                raise asyncio.CancelledError(f"Send error: {e}")
        
        subscription_task = asyncio.create_task(
            broker.subscribe_orderbook_async(symbol, send_callback)
        )
        await subscription_task
    
    except WebSocketDisconnect:
        is_connected = False
    except asyncio.CancelledError:
        is_connected = False
    except Exception as e:
        is_connected = False
        print(f"❌ Orderbook WebSocket error: {e}")
    finally:
        is_connected = False
        if subscription_task and not subscription_task.done():
            subscription_task.cancel()
            try:
                await subscription_task
            except (asyncio.CancelledError, Exception):
                pass
        print(f"🔌 Orderbook closed: {broker_name}/{symbol}")

@app.websocket("/ws/trade/{broker_name}/{symbol}")
async def websocket_trade(ws: WebSocket, broker_name: str, symbol: str):
    await ws.accept()
    print(f"✅ Trade connected: {broker_name}/{symbol}")
    
    broker = None
    subscription_task = None
    is_connected = True
    
    try:
        broker = BrokerFactory.create_broker(broker_name)
        
        async def send_callback(data: dict):
            nonlocal is_connected
            if not is_connected:
                raise asyncio.CancelledError("Client disconnected")
            try:
                await ws.send_json(data)
            except WebSocketDisconnect:
                is_connected = False
                raise asyncio.CancelledError("Client disconnected")
            except Exception as e:
                is_connected = False
                raise asyncio.CancelledError(f"Send error: {e}")
        
        subscription_task = asyncio.create_task(
            broker.subscribe_trade_price_async(symbol, send_callback)
        )
        await subscription_task
    
    except WebSocketDisconnect:
        is_connected = False
    except asyncio.CancelledError:
        is_connected = False
    except Exception as e:
        is_connected = False
        print(f"❌ Trade WebSocket error: {e}")
    finally:
        is_connected = False
        if subscription_task and not subscription_task.done():
            subscription_task.cancel()
            try:
                await subscription_task
            except (asyncio.CancelledError, Exception):
                pass
        print(f"🔌 Trade closed: {broker_name}/{symbol}")

@app.websocket("/ws")
async def websocket_proxy(ws: WebSocket):
    await ws.accept()

    payload = {}
    try:
        payload = await ws.receive_json()
    except:
        pass
    
    broker = None
    subscription_task = None
    is_connected = True
    
    try:
        broker = BrokerFactory.create_broker(payload['broker_name'])
        
        # 비동기 콜백 - 데이터를 즉시 클라이언트로 전송 (프록시)
        async def send_callback(data: dict):
            nonlocal is_connected
            
            if not is_connected:
                raise asyncio.CancelledError("Client disconnected")
            try:
                await ws.send_json(data)
            except WebSocketDisconnect:
                # 클라이언트 연결 끊김 - 플래그 설정 후 취소
                is_connected = False
                raise asyncio.CancelledError("Client disconnected")
            except Exception as e:
                # 기타 오류 - 플래그 설정 후 취소
                is_connected = False
                raise asyncio.CancelledError(f"Send error: {e}")
        
        # 비동기 구독 시작 - Binance → 즉시 → Client (프록시 방식)
        match payload['ws_type']:
            case "orderbook":
                subscription_task = asyncio.create_task(
                    broker.subscribe_orderbook_async(payload['symbol'], send_callback)
                )
            case "trade_price":
                subscription_task = asyncio.create_task(
                    broker.subscribe_trade_price_async(payload['symbol'], send_callback)
                )
        
        # Task가 완료될 때까지 대기 (WebSocket 연결 유지)
        await subscription_task
    
    except WebSocketDisconnect:
        is_connected = False
        print(f"Client disconnected")
    
    except asyncio.CancelledError:
        is_connected = False
        # 정상적인 취소, 로그 불필요
    
    except Exception as e:
        is_connected = False
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 구독 태스크 취소
        is_connected = False
        if subscription_task and not subscription_task.done():
            subscription_task.cancel()
            try:
                await subscription_task
            except (asyncio.CancelledError, Exception):
                pass  # 취소 시 발생하는 모든 예외 무시
        
        print(f"WebSocket closed")

def main():
    print(f"Starting {SERVER_NAME}...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVER_PORT,
        log_level="info"
    )

if __name__ == "__main__":
    main()