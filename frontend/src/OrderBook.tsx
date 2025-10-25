import React, { useState } from 'react';

// --- 타입 정의 ---

// 호가창 데이터 행
interface Order {
  price: number;
  size: number;
}

// 호가창 행 컴포넌트 Props
interface OrderBookRowProps {
  price: number;
  size: number;
  type: 'ask' | 'bid';
  displayCount: number;
}

// 호가창 행 컴포넌트
const OrderBookRow: React.FC<OrderBookRowProps> = ({ price, size, type, displayCount }) => {
  const isAsk = type === 'ask';
  const textColor = isAsk ? 'text-red-500' : 'text-green-500';
  const barColor = isAsk ? 'bg-red-900/50' : 'bg-green-900/50';
  
  // 임의의 백분율로 바 너비 설정 (시각적 효과)
  const barWidth = Math.min(size * 20, 100); 

  // 호가 개수에 따라 동적으로 패딩 조절
  const paddingClass = displayCount <= 5 ? 'p-2' : 
                      displayCount <= 10 ? 'p-1.5' : 
                      displayCount <= 15 ? 'p-1' : 'p-0.5';
  
  const textSizeClass = displayCount <= 5 ? 'text-sm' : 
                       displayCount <= 10 ? 'text-xs' : 
                       displayCount <= 15 ? 'text-[11px]' : 'text-[10px]';

  return (
    <div className={`relative flex justify-between items-center ${paddingClass} ${textSizeClass} rounded-sm overflow-hidden hover:bg-gray-700 transition-colors`}>
      {/* 시각적 깊이 바 */}
      <div 
        className={`absolute top-0 bottom-0 ${isAsk ? 'right-0' : 'left-0'} ${barColor} z-0`}
        style={{ width: `${barWidth}%` }}
      ></div>
      
      {/* 텍스트 컨텐츠 */}
      <span className={`z-10 font-mono ${textColor}`}>{price.toLocaleString()}</span>
      <span className="z-10 font-mono">{size.toFixed(2)}</span>
    </div>
  );
};

// --- 호가창 컴포넌트 ---
const OrderBook: React.FC = () => {
  // 호가 표시 개수 상태 (1~20개)
  const [displayCount, setDisplayCount] = useState<number>(20);

  // 전체 목(mock) 데이터 (최대 20개)
  const generateMockAsks = (count: number): Order[] => {
    const asks: Order[] = [];
    const basePrice = 60000;
    for (let i = 0; i < count; i++) {
      asks.push({
        price: basePrice + (i + 1) * 50,
        size: Math.random() * 3 + 0.1
      });
    }
    return asks.sort((a, b) => b.price - a.price);
  };

  const generateMockBids = (count: number): Order[] => {
    const bids: Order[] = [];
    const basePrice = 59950;
    for (let i = 0; i < count; i++) {
      bids.push({
        price: basePrice - i * 50,
        size: Math.random() * 3 + 0.1
      });
    }
    return bids.sort((a, b) => b.price - a.price);
  };

  const asks: Order[] = generateMockAsks(20).slice(0, displayCount);
  const bids: Order[] = generateMockBids(20).slice(0, displayCount);

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-lg h-[1000px] flex flex-col">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-lg font-semibold text-gray-200">Order Book</h3>
        
        {/* 호가 개수 조절 컨트롤 */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setDisplayCount(Math.max(1, displayCount - 1))}
            disabled={displayCount <= 1}
            className="px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded text-xs transition-colors"
          >
            -
          </button>
          <span className="text-xs text-gray-400 min-w-[40px] text-center">
            {displayCount}개
          </span>
          <button
            onClick={() => setDisplayCount(Math.min(20, displayCount + 1))}
            disabled={displayCount >= 20}
            className="px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded text-xs transition-colors"
          >
            +
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-2 text-xs text-gray-400">
        <span>Price</span>
        <span className="text-right">Amount</span>
      </div>
      
      {/* 호가 영역 - 스크롤 없이 모두 표시 */}
      <div className="flex-1 overflow-hidden flex flex-col min-h-0">
        {/* 매도 (Asks) */}
        <div className="flex-1 flex flex-col justify-end">
          {asks.map((ask, index) => (
            <OrderBookRow 
              key={`ask-${ask.price}-${index}`} 
              price={ask.price} 
              size={ask.size} 
              type="ask"
              displayCount={displayCount}
            />
          ))}
        </div>

        {/* 현재가 (임시) */}
        <div className={`${displayCount <= 10 ? 'py-2 my-2' : 'py-1 my-1'} border-y border-gray-600 flex-shrink-0`}>
          <span className={`${displayCount <= 10 ? 'text-xl' : 'text-lg'} font-bold text-white flex justify-center`}>
            60,000
          </span>
        </div>
        
        {/* 매수 (Bids) */}
        <div className="flex-1 flex flex-col">
          {bids.map((bid, index) => (
            <OrderBookRow 
              key={`bid-${bid.price}-${index}`} 
              price={bid.price} 
              size={bid.size} 
              type="bid"
              displayCount={displayCount}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default OrderBook;
