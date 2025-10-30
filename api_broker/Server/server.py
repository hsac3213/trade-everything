from ..BrokerCommon.BrokerFactory import BrokerFactory
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import queue
import json
import traceback

from ..Binance.BinanceBroker import BinanceBroker

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

@app.websocket("/ws/orderbook/{broker_name}/{symbol}")
async def websocket_orderbook_proxy(ws: WebSocket, broker_name: str, symbol: str):
    """완전 비동기 프록시 방식 - 바이낸스 데이터를 즉시 클라이언트로 전송"""
    await ws.accept()
    print(f"✅ Client connected: {broker_name}/{symbol}")
    
    broker = None
    
    try:
        # 브로커 인스턴스 생성
        broker = BrokerFactory.create_broker(broker_name)
        
        # 비동기 콜백 - 데이터를 즉시 클라이언트로 전송 (프록시)
        async def send_callback(data: dict):
            try:
                await ws.send_json(data)
            except Exception as e:
                print(f"❌ Error sending data to client: {e}")
                raise  # 연결 끊김 시 상위로 전파
        
        # 비동기 구독 시작 - Binance → 즉시 → Client (프록시 방식)
        await broker.subscribe_orderbook_async(symbol, send_callback)
    
    except WebSocketDisconnect:
        print(f"🔌 Client disconnected: {broker_name}/{symbol}")
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"🔌 WebSocket closed: {broker_name}/{symbol}")


@app.websocket("/ws")
async def websocket_handler(ws: WebSocket):
    await ws.accept()
    print("[ websocket_handler ]")
    print("[ first ]")

    try:
        payload = json.loads(await ws.receive_text())
        print(payload)

        broker = BrokerFactory.create_broker(payload["broker_name"])
    except json.JSONDecodeError:
        resp = {
            "message": "Failed to decode json payload.",
        }
        await ws.send_text(json.dumps(resp))
    except Exception as e:
        print(traceback.format_exec())
    
    try:      
        while True:
            try:
                payload = json.loads(await ws.receive_text())
                print(payload)
                
                resp = {
                    "message": "ok",
                }
                await ws.send_text(json.dumps(resp))
            except json.JSONDecodeError:
                resp = {
                    "message": "Failed to decode json payload."
                }
                await ws.send_text(json.dumps(resp))
    except WebSocketDisconnect:
        print("WebSocketDisconnect")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        print(traceback.format_exc())   
    finally:
        pass

@app.websocket("/ws_old")
async def websocket_handler_old(ws: WebSocket):
    await ws.accept()
    print("[ websocket_handler ]")
    
    broker = None
    
    try:
        print(ws.receive_text())

        # 브로커 인스턴스 생성
        broker = BrokerFactory.create_broker(broker_name)
        
        # 콜백 함수: 호가 데이터를 WebSocket으로 전송
        async def send_orderbook(data: dict):
            try:
                await ws.send_json(data)
            except Exception as e:
                print(f"❌ Error sending data: {e}")
        
        # 동기 콜백에서 비동기 send 호출
        data_queue_sync = queue.Queue()
        
        def sync_callback(data: dict):
            data_queue_sync.put(data)
        
        # 호가 구독 시작
        broker.subscribe_orderbook(symbol, sync_callback)
        
        # 별도 태스크로 큐 모니터링
        async def queue_monitor():
            while True:
                try:
                    # 큐에서 데이터 가져오기 (non-blocking)
                    while not data_queue_sync.empty():
                        data = data_queue_sync.get_nowait()
                        await ws.send_json(data)
                    await asyncio.sleep(0.01)  # 10ms 대기
                except Exception as e:
                    print(f"❌ Queue monitor error: {e}")
                    break
        
        # 큐 모니터링 시작
        monitor_task = asyncio.create_task(queue_monitor())
        
        # 연결 유지 (클라이언트가 연결을 끊을 때까지)
        try:
            while True:
                # 클라이언트로부터 메시지 대기 (ping/pong 등)
                data = await ws.receive_text()
                if data == "ping":
                    await ws.send_text("pong")
        except WebSocketDisconnect:
            print(f"🔌 Client disconnected: {broker_name}/{symbol}")
            monitor_task.cancel()
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 구독 해제
        if broker and hasattr(broker, 'unsubscribe_orderbook'):
            broker.unsubscribe_orderbook()
        print(f"🔌 WebSocket closed: {broker_name}/{symbol}")

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