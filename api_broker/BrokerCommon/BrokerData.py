from ..Common.DBManager import get_db_conn
from ..Common.Debug import *

from typing import List, Dict, Any, Callable, Awaitable
from datetime import datetime, timedelta
import traceback

def get_candles_from_db(
    broker_name: str,
    symbol: str,
    interval: str,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    DB로부터 캔들 데이터를 가져옴
    """

    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    broker_name, symbol, interval,
                    open_time, close_time,
                    open, high, low, close, volume,
                    quote_volume, trade_count,
                    taker_buy_base_asset_volume, taker_buy_quote_asset_volume,
                    inserted_at
                FROM candle_data
                WHERE broker_name = %s
                    AND symbol = %s
                    AND interval = %s
            """
            
            params = [broker_name, symbol, interval]
            
            if start_time:
                query += " AND open_time >= %s"
                params.append(start_time)
            
            if end_time:
                query += " AND open_time <= %s"
                params.append(end_time)
            
            # 가져오는 것은 최신 데이터부터 가져오기
            query += " ORDER BY open_time DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            cursor.close()
        
        candles = []
        for row in rows:
            candles.append({
                "broker_name": row["broker_name"],
                "symbol": row["symbol"],
                "interval": row["interval"],
                "open_time": row["open_time"],
                "close_time": row["close_time"],
                "open": float(row["open"]) if row["open"] else None,
                "high": float(row["high"]) if row["high"] else None,
                "low": float(row["low"]) if row["low"] else None,
                "close": float(row["close"]) if row["close"] else None,
                "volume": float(row["volume"]) if row["volume"] else None,
                "quote_volume": float(row["quote_volume"]) if row["quote_volume"] else None,
                "trade_count": row["trade_count"],
                "taker_buy_base_asset_volume": float(row["taker_buy_base_asset_volume"]) if row["taker_buy_base_asset_volume"] else None,
                "taker_buy_quote_asset_volume": float(row["taker_buy_quote_asset_volume"]) if row["taker_buy_quote_asset_volume"] else None,
                "inserted_at": row["inserted_at"],
            })
        
        # 정렬은 오름차순으로
        candles.reverse()
        return candles
        
    except Exception as e:
        Error(f"Exception")
        traceback.print_exc()
        return []

def insert_candles_to_db(candles: List[Dict[str, Any]]):
        """
        캔들 데이터를 DB에 저장(중복 데이터는 무시)
        현재 생성중인 캔들은 저장하지 않음
        """
        try:
            with get_db_conn() as conn:
                cursor = conn.cursor()
                
                insert_query = """
                    INSERT INTO candle_data (
                        broker_name, symbol, interval, 
                        open_time, close_time,
                        open, high, low, close,
                        volume, quote_volume, trade_count,
                        taker_buy_base_asset_volume, taker_buy_quote_asset_volume
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s
                    )
                    ON CONFLICT (broker_name, symbol, interval, open_time) 
                    DO NOTHING;
                """
                
                for candle in candles:
                    # 현재 생성중인 캔들은 무시
                    if candle["interval"] == "1d":
                        candle_close_time = candle["open_time"] + timedelta(days=1)
                    elif candle["interval"] == "1h":
                        candle_close_time = candle["open_time"] + timedelta(hours=1)

                    if datetime.now() < candle_close_time:
                        #print(f"생성중인 캔들 무시 : {datetime.strftime(candle["close_time"], "%Y-%m-%d %H:%M:%S")}")
                        #print(f"{datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")} < {datetime.strftime(candle_close_time, "%Y-%m-%d %H:%M:%S")}")
                        continue
                    
                    # 밀리초 타임스탬프를 그대로 전달(PostgreSQL에서 자동 변환)
                    cursor.execute(insert_query, (
                        candle["broker_name"],
                        candle["symbol"],
                        candle["interval"],
                        candle["open_time"],
                        candle["close_time"],

                        candle["open"],
                        candle["high"],
                        candle["low"],
                        candle["close"],
                        candle["volume"],
                        candle["quote_volume"],
                        candle["trade_count"],
                        candle["taker_buy_base_asset_volume"],
                        candle["taker_buy_quote_asset_volume"],
                    ))
                
                conn.commit()
                cursor.close()
            
        except Exception as e:
            Error(f"Exception")
            traceback.print_exc()