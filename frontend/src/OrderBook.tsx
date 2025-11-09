import React, { useState, useEffect, useRef } from 'react';
import { useSharedTradeWebSocket } from './useSharedTradeWebSocket';

// --- 타입 정의 ---

// 호가창 데이터 행
interface Order {
  price: number;
  quantity: number;
}

interface OrderBookProps {
  broker?: string;
  symbol?: string;
}

// 호가창 행 컴포넌트 Props
interface OrderBookRowProps {
  price: number;
  quantity: number;
  type: 'ask' | 'bid';
  displayCount: number;
  maxTotal: number;  // Total 값의 최대값 (bar 너비 계산용)
}

// 호가창 행 컴포넌트
const OrderBookRow: React.FC<OrderBookRowProps> = ({ price, quantity, type, displayCount, maxTotal }) => {
  const isAsk = type === 'ask';
  const textColor = isAsk ? 'text-red-500' : 'text-green-500';
  const barColor = isAsk ? 'bg-red-900/50' : 'bg-green-900/50';
  
  // Total 계산 (Price * Amount)
  const total = price * quantity;
  
  // Total을 기준으로 bar 너비 설정 (2배로 증폭)
  const barWidth = maxTotal > 0 ? Math.min((total / maxTotal) * 100 * 2, 100) : 0;

  // Total 포맷팅 함수 (K, M 표기)
  const formatTotal = (value: number): string => {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(2) + 'M';
    } else if (value >= 1000) {
      return (value / 1000).toFixed(2) + 'K';
    } else {
      return value.toFixed(5);
    }
  };

  // 호가 개수에 따라 동적으로 패딩 조절
  const paddingClass = displayCount <= 5 ? 'p-2' : 
                      displayCount <= 10 ? 'p-1.5' : 
                      displayCount <= 15 ? 'p-1' : 'p-0.5';
  
  const textSizeClass = displayCount <= 5 ? 'text-sm' : 
                       displayCount <= 10 ? 'text-xs' : 
                       displayCount <= 15 ? 'text-[11px]' : 'text-[10px]';

  return (
    <div className={`relative grid grid-cols-3 gap-2 items-center ${paddingClass} ${textSizeClass} rounded-sm overflow-hidden hover:bg-gray-700 transition-colors`}>
      {/* 시각적 깊이 바 */}
      <div 
        className={`absolute top-0 bottom-0 right-0 ${barColor} z-0`}
        style={{ width: `${barWidth}%` }}
      ></div>
      
      {/* Price */}
      <span className={`z-10 font-mono ${textColor}`}>{price.toLocaleString()}</span>
      
      {/* Amount */}
      <span className="z-10 font-mono text-right">{quantity.toFixed(5)}</span>
      
      {/* Total */}
      <span className="z-10 font-mono text-right">{formatTotal(total)}</span>
    </div>
  );
};

// --- 호가창 컴포넌트 ---
const OrderBook: React.FC<OrderBookProps> = ({ 
  broker = 'Binance', 
  symbol = 'btcusdt' 
}) => {
  // 호가 표시 개수 상태 (1~20개)
  const [displayCount, setDisplayCount] = useState<number>(20);
  const [asks, setAsks] = useState<Order[]>([]);
  const [bids, setBids] = useState<Order[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  
  // 공유 WebSocket Hook으로 실시간 체결가 구독
  const tradeData = useSharedTradeWebSocket(broker, symbol);
  const currentPrice = tradeData?.price ? Number(tradeData.price) : 0;

  // WebSocket 연결 (호가창 데이터용)
  useEffect(() => {
    let isMounted = true; // cleanup 플래그
    const ws = new WebSocket(`ws://localhost:8001/ws/orderbook/${broker}/${symbol}`);
    wsRef.current = ws;

    ws.onopen = () => {
      if (isMounted) {
        console.log(`✅ Connected to ${broker} ${symbol} orderbook`);
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
        
        // 매수/매도 호가 업데이트
        if (data.bids && data.asks) {
          setBids(data.bids);
          setAsks(data.asks);
        }
        
      } catch (error) {
        console.error('Error parsing orderbook data:', error);
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

  // 전체 목 데이터 제거, 실시간 데이터 사용
  const displayedAsks = asks.slice(0, displayCount);
  const displayedBids = bids.slice(0, displayCount);

  return (
    <div className="bg-gray-800 p-3 rounded-lg shadow-lg h-[900px] flex flex-col">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-3">
          <h3 className="text-base font-semibold text-gray-200">Order Book</h3>
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
      
      <div className="grid grid-cols-3 gap-2 text-xs text-gray-400 pb-0.5">
        <span>Price</span>
        <span className="text-right">Amount</span>
        <span className="text-right">Total</span>
      </div>
      
      {/* 호가 영역 - 스크롤 없이 모두 표시 */}
      <div className="flex-1 overflow-hidden flex flex-col min-h-0">
        {/* 매도 (Asks) - 역순으로 표시하되 상단부터 */}
        <div className="flex flex-col">
          {displayedAsks.slice().reverse().map((ask, index) => {
            // 상위 5개의 Total 평균 계산
            const allTotals = [...displayedAsks, ...displayedBids]
              .map(item => item.price * item.quantity)
              .filter(total => total > 0)
              .sort((a, b) => b - a);
            
            const topN = 5;
            const avgTopTotal = allTotals.length > 0
              ? allTotals.slice(0, Math.min(topN, allTotals.length))
                  .reduce((sum, val) => sum + val, 0) / Math.min(topN, allTotals.length)
              : 1;
            
            return (
              <OrderBookRow 
                key={`ask-${ask.price}-${index}`} 
                price={ask.price} 
                quantity={ask.quantity} 
                type="ask"
                displayCount={displayCount}
                maxTotal={avgTopTotal}
              />
            );
          })}
        </div>

        {/* 현재가 (실시간 체결가) */}
        <div className={`${displayCount <= 10 ? 'py-2 my-2' : 'py-1 my-1'} border-y border-gray-600 flex-shrink-0`}>
          <span className={`${displayCount <= 10 ? 'text-xl' : 'text-lg'} font-bold text-white flex justify-center`}>
            {currentPrice > 0 ? currentPrice.toLocaleString() : 
             (displayedBids.length > 0 ? displayedBids[0].price.toLocaleString() : '---')}
          </span>
        </div>
        
        {/* 매수 (Bids) */}
        <div className="flex-1 flex flex-col">
          {displayedBids.map((bid, index) => {
            // 상위 5개의 Total 평균 계산
            const allTotals = [...displayedAsks, ...displayedBids]
              .map(item => item.price * item.quantity)
              .filter(total => total > 0)
              .sort((a, b) => b - a);
            
            const topN = 5;
            const avgTopTotal = allTotals.length > 0
              ? allTotals.slice(0, Math.min(topN, allTotals.length))
                  .reduce((sum, val) => sum + val, 0) / Math.min(topN, allTotals.length)
              : 1;
            
            return (
              <OrderBookRow 
                key={`bid-${bid.price}-${index}`} 
                price={bid.price} 
                quantity={bid.quantity} 
                type="bid"
                displayCount={displayCount}
                maxTotal={avgTopTotal}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default OrderBook;
