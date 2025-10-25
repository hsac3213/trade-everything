import React, { useState } from 'react';
import SimpleChart from './CandleChart';
import OrderBook from './OrderBook';
import Order from './Order';
import Pair from './Pair';
import OpenOrder from './OpenOrder';

// --- 차트 플레이스홀더 ---
const ChartPlaceholder: React.FC = () => {
  const [timeframe, setTimeframe] = useState<string>('1D');
  
  const timeframes = [
    { value: 'Tick', label: 'Tick' },
    { value: '1S', label: '1S' },
    { value: '1M', label: '1M' },
    { value: '1H', label: '1H' },
    { value: '1D', label: '1D' },
  ];

  return (
    <div className="w-[1200px] bg-gray-800 rounded-lg shadow-lg flex flex-col">
      {/* 주기 선택 버튼들 - 상단 영역 */}
      <div className="p-3 border-b border-gray-700">
        <div className="flex gap-1">
          {timeframes.map((tf) => (
            <button
              key={tf.value}
              onClick={() => setTimeframe(tf.value)}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                timeframe === tf.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-900 text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* 차트 영역 */}
      <div className="flex items-start justify-center h-[460px]">
        <SimpleChart height={460} width="1200px" />
      </div>
      
      {/* 하단 영역: 거래 페어 선택 & Open Orders */}
      <div className="flex gap-4 h-[460px] p-4">
        {/* 좌측: 거래 페어 선택 */}
        <Pair />
        
        {/* 우측: Open Orders */}
        <OpenOrder />
      </div>
    </div>
  );
};

// --- 메인 앱 컴포넌트 ---
const App: React.FC = () => {
  const [exchange, setExchange] = useState<string>('KIS');

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4 lg:p-8 font-sans">
      <header className="mb-6">
        <div className="flex justify-between items-start mb-4">
          {/* 좌측: 거래소 선택 */}
          <div className="flex items-center gap-3">
            <select
              id="exchange-select"
              value={exchange}
              onChange={(e) => setExchange(e.target.value)}
              className="bg-gray-800 text-white border border-gray-600 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              <option value="KIS">KIS</option>
              <option value="LS">LS</option>
              <option value="UPBit">UPBit</option>
              <option value="Binance">Binance</option>
            </select>
          </div>

          {/* 중앙: 타이틀 */}
          <div className="flex-1 text-center">
            <h1 className="text-3xl font-bold text-gray-100">
              Trade Everything
            </h1>
          </div>

          {/* 우측: 빈 공간 (레이아웃 균형용) */}
          <div className="w-[150px]"></div>
        </div>
      </header>

      {/* 메인 레이아웃 */}
      <div className="flex flex-col lg:flex-row gap-6 mx-auto justify-center">
        
        {/* 왼쪽: 호가창 */}
        <aside className="w-full lg:w-auto">
          <OrderBook />
        </aside>

        {/* 중앙: 차트 */}
        <main className="w-full lg:w-auto flex">
          <ChartPlaceholder />
        </main>

        {/* 오른쪽: 주문 */}
        <aside className="w-full lg:w-auto">
          <Order />
        </aside>

      </div>
    </div>
  );
}

export default App;
