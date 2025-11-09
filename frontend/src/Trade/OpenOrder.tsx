import React from 'react';

// --- Open Orders 컴포넌트 ---
const OpenOrder: React.FC = () => {
  const openOrders = [
    { id: '1', pair: 'BTC/USDT', side: 'buy', price: '43,000.00', amount: '0.5', filled: '0%', status: 'open' },
    { id: '2', pair: 'ETH/USDT', side: 'sell', price: '2,300.00', amount: '2.5', filled: '30%', status: 'partial' },
    { id: '3', pair: 'SOL/USDT', side: 'buy', price: '95.00', amount: '10', filled: '0%', status: 'open' },
  ];

  return (
    <div className="flex-1 bg-gray-900 rounded-lg p-3 flex flex-col">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-base font-semibold text-gray-200">Open Orders</h3>
        
        {/* Cancel All 버튼 */}
        <button 
          className="px-4 py-1.5 bg-red-600 hover:bg-red-700 rounded text-sm font-medium transition-colors disabled:bg-gray-600 disabled:cursor-not-allowed"
          disabled={openOrders.length === 0}
        >
          Cancel All
        </button>
      </div>
      
      {/* 주문 목록 헤더 */}
      <div className="grid grid-cols-6 gap-2 mb-1 text-xs text-gray-400 font-medium">
        <span>페어</span>
        <span>구분</span>
        <span>가격</span>
        <span>수량</span>
        <span>체결률</span>
        <span className="text-center">취소</span>
      </div>
      
      {/* 주문 목록 */}
      <div className="overflow-y-auto space-y-1.5 max-h-[400px]">
        {openOrders.length > 0 ? (
          openOrders.map((order) => (
            <div
              key={order.id}
              className="grid grid-cols-6 gap-2 p-2 bg-gray-800 rounded-md text-sm items-center"
            >
              <span className="font-mono text-xs">{order.pair}</span>
              <span className={`font-semibold ${order.side === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                {order.side === 'buy' ? '매수' : '매도'}
              </span>
              <span className="font-mono text-xs">{order.price}</span>
              <span className="font-mono text-xs">{order.amount}</span>
              <span className="text-xs text-gray-400">{order.filled}</span>
              <button className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs transition-colors">
                취소
              </button>
            </div>
          ))
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            주문 내역이 없습니다
          </div>
        )}
      </div>
    </div>
  );
};

export default OpenOrder;
