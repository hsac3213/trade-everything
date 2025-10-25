from ..BrokerCommon.BrokerFactory import BrokerFactory
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI(title="Trade Everything API Broker")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Trade Everything API Broker Server",
        "available_brokers": BrokerFactory.get_available_brokers()
    }

@app.get("/brokers")
def get_brokers():
    """사용 가능한 브로커 목록 조회"""
    return {
        "brokers": BrokerFactory.get_available_brokers()
    }

@app.websocket("/ws/orderbook/{broker_name}/{symbol}")
async def websocket_orderbook(websocket: WebSocket, broker_name: str, symbol: str):
    """
    실시간 호가 WebSocket 엔드포인트
    
    예: ws://localhost:8001/ws/orderbook/Binance/btcusdt
    """
    await websocket.accept()
    print(f"✅ WebSocket client connected: {broker_name}/{symbol}")
    
    broker = None
    
    try:
        # 브로커 인스턴스 생성
        broker = BrokerFactory.create_broker(broker_name)
        
        # 콜백 함수: 호가 데이터를 WebSocket으로 전송
        async def send_orderbook(data: dict):
            try:
                await websocket.send_json(data)
            except Exception as e:
                print(f"❌ Error sending data: {e}")
        
        # 동기 콜백에서 비동기 send 호출
        import queue
        import threading
        
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
                        await websocket.send_json(data)
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
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
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
    print("🚀 Starting Trade Everything API Broker Server...")
    print(f"📋 Available brokers: {BrokerFactory.get_available_brokers()}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )

if __name__ == "__main__":
    main()