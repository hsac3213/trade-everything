import React, { useState, useEffect, useRef } from 'react';

// --- 타입 정의 ---

// 체결 데이터
interface Trade {
  price: number;
  size: number;
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
      <span className={`font-mono ${textColor}`}>{trade.price.toLocaleString()}</span>
      
      {/* Amount */}
      <span className="font-mono text-right">{trade.size.toFixed(5)}</span>
      
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

  // WebSocket 연결 (체결 데이터)
  useEffect(() => {
    // TODO: 실제 체결 데이터 WebSocket 연결 구현
    // 현재는 목 데이터로 표시
    
    const mockTrades: Trade[] = [
      { price: 43250.50, size: 0.12345, time: '14:32:45', isBuyerMaker: false },
      { price: 43251.00, size: 0.08920, time: '14:32:46', isBuyerMaker: true },
      { price: 43250.75, size: 0.15670, time: '14:32:47', isBuyerMaker: false },
      { price: 43252.25, size: 0.05430, time: '14:32:48', isBuyerMaker: false },
      { price: 43251.50, size: 0.22100, time: '14:32:49', isBuyerMaker: true },
      { price: 43250.00, size: 0.18890, time: '14:32:50', isBuyerMaker: true },
      { price: 43251.75, size: 0.09870, time: '14:32:51', isBuyerMaker: false },
      { price: 43253.00, size: 0.14560, time: '14:32:52', isBuyerMaker: false },
      { price: 43252.50, size: 0.11230, time: '14:32:53', isBuyerMaker: true },
      { price: 43251.25, size: 0.06780, time: '14:32:54', isBuyerMaker: false },
    ];
    
    setTrades(mockTrades);
    setIsConnected(false); // 목 데이터이므로 false
    
    // Cleanup
    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [broker, symbol]);

  return (
    <div className="bg-gray-800 p-3 rounded-lg shadow-lg h-[426px] flex flex-col">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-3">
          <h3 className="text-base font-semibold text-gray-200">Trade Price</h3>
          <div className="flex items-center gap-2">
            <div 
              className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-500'}`}
            />
            <span className="text-xs text-gray-400">
              {isConnected ? 'Live' : 'Mock Data'}
            </span>
          </div>
        </div>
      </div>
      
      {/* 헤더 */}
      <div className="grid grid-cols-3 gap-2 mb-1 text-xs text-gray-400">
        <span>Price</span>
        <span className="text-right">Amount</span>
        <span className="text-right">Time</span>
      </div>
      
      {/* 체결 내역 영역 */}
      <div className="flex-1 overflow-y-auto space-y-0.5">
        {trades.map((trade, index) => (
          <TradePriceRow 
            key={`trade-${index}`} 
            trade={trade}
          />
        ))}
      </div>
    </div>
  );
};

export default TradePrice;
