import React, { useState, useEffect, useRef } from 'react';

// --- 타입 정의 ---

// 체결 데이터
interface Trade {
  price: number;
  quantity: number;
  time: string;
  isBuyerMaker: boolean; // true: 매도 체결, false: 매수 체결
}

interface TradePriceProps {
  broker?: string;
  symbol?: string;
}

// --- 체결가격 행 컴포넌트 ---
interface TradePriceRowProps {
  trade: Trade;
}

const TradePriceRow: React.FC<TradePriceRowProps> = ({ trade }) => {
  const textColor = trade.isBuyerMaker ? 'text-red-500' : 'text-green-500';
  
  return (
    <div className="grid grid-cols-3 gap-2 items-center p-1 text-xs rounded-sm hover:bg-gray-700 transition-colors">
      {/* Price */}
      <span className={`font-mono ${textColor}`}>{Number(trade.price).toLocaleString()}</span>
      
      {/* Amount */}
      <span className="font-mono text-right">{Number(trade.quantity).toFixed(5)}</span>
      
      {/* Time */}
      <span className="font-mono text-right text-gray-400">{trade.time}</span>
    </div>
  );
};

// --- 체결가격 컴포넌트 ---
const TradePrice: React.FC<TradePriceProps> = ({ 
  broker = 'Binance', 
  symbol = 'btcusdt' 
}) => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const MAX_TRADES = 30; // 최대 30개까지 보관

  // WebSocket 연결 (체결 데이터)
  useEffect(() => {
    let isMounted = true;
    const ws = new WebSocket(`ws://localhost:8001/ws/trade/${broker}/${symbol}`);
    wsRef.current = ws;

    ws.onopen = () => {
      if (isMounted) {
        console.log(`✅ Connected to ${broker} ${symbol} trade price`);
        setIsConnected(true);
      }
    };

    ws.onmessage = (event) => {
      if (!isMounted) return; // 언마운트된 경우 무시
      
      try {
        const data = JSON.parse(event.data);
        
        // ping 메시지 무시
        if (data.type === 'ping') {
          return;
        }
        
        // 체결 데이터 업데이트
        if (data.price && data.quantity !== undefined) {
          const newTrade: Trade = {
            price: data.price,
            quantity: data.quantity,
            time: data.time || new Date().toLocaleTimeString('en-US', { hour12: false }),
            isBuyerMaker: data.isBuyerMaker || false,
          };
          
          // 새 체결을 맨 위에 추가하고 최대 30개까지만 유지
          setTrades(prevTrades => [newTrade, ...prevTrades].slice(0, MAX_TRADES));
        }
        
      } catch (error) {
        console.error('Error parsing trade data:', error);
      }
    };

    ws.onerror = (error) => {
      if (isMounted) {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      }
    };

    ws.onclose = () => {
      if (isMounted) {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
      }
    };

    // Cleanup: 컴포넌트 언마운트 시 연결 해제
    return () => {
      console.log('🧹 Cleaning up WebSocket connection');
      isMounted = false; // 언마운트 표시
      
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      
      wsRef.current = null;
    };
  }, [broker, symbol]);

  return (
    <div className="bg-gray-800 p-3 rounded-lg shadow-lg h-[426px] flex flex-col">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-3">
          <h3 className="text-base font-semibold text-gray-200">Trade Price</h3>
          <div className="flex items-center gap-2">
            <div 
              className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
            />
            <span className="text-xs text-gray-400">
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>
      
      {/* 헤더 */}
      <div className="grid grid-cols-3 gap-2 mb-1 text-xs text-gray-400">
        <span 
          className="cursor-help relative group"
          title="Red: Seller filled (buyer's order was waiting) | Green: Buyer filled (seller's order was waiting)"
        >
          Price
          {/* 툴팁 - 위쪽으로 표시 */}
          <div className="absolute left-0 bottom-full mb-1 w-64 bg-gray-900 text-white text-xs rounded-md p-2 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50 border border-gray-700">
            <div className="space-y-1">
              <div className="text-red-400">
                Red: Seller filled (buyer's order was waiting)
              </div>
              <div className="text-green-400">
                Green: Buyer filled (seller's order was waiting)
              </div>
            </div>
          </div>
        </span>
        <span className="text-right">Amount</span>
        <span className="text-right">Time</span>
      </div>
      
      {/* 체결 내역 영역 - 스크롤 가능, 최대 30개 */}
      <div className="flex-1 overflow-y-auto space-y-0.5">
        {trades.length > 0 ? (
          trades.map((trade, index) => (
            <TradePriceRow 
              key={`trade-${trade.time}-${index}`} 
              trade={trade}
            />
          ))
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">
            {isConnected ? '체결 대기 중...' : '연결 대기 중...'}
          </div>
        )}
      </div>
    </div>
  );
};

export default TradePrice;
