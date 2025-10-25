from ..BrokerCommon.BrokerFactory import BrokerFactory
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Trade Everything API Broker")

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