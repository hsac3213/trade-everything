import React, { useState } from 'react';
import SimpleChart from './CandleChart';
import OrderBook from './OrderBook';
import Order from './Order';
import Pair from './Pair';
import OpenOrder from './OpenOrder';
import TradePrice from './TradePrice';

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
    <div className="w-[1300px] bg-gray-800 rounded-lg shadow-lg flex flex-col">
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
        <SimpleChart height={460} width="1300px" />
      </div>
      
      {/* 하단 영역: 거래 페어 선택 & Open Orders */}
      <div className="flex gap-4 p-4">
        {/* 좌측: 주문 */}
        <Order />
        
        {/* 우측: Open Orders */}
        <OpenOrder />
      </div>
    </div>
  );
};

const Trade: React.FC = () => {
  const [exchange, setExchange] = useState<string>('Binance');
  const [symbol, setSymbol] = useState<string>('btcusdt');

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      {/* 왼쪽: 거래소 선택 + 호가창 */}
      <aside className="w-full lg:w-[300px] flex flex-col gap-3">
        {/* 거래소 선택 콤보박스 */}
        <select
          id="exchange-select"
          value={exchange}
          onChange={(e) => setExchange(e.target.value)}
          className="bg-gray-800 text-white border border-gray-600 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
        >
          <option value="Binance">Binance</option>
          <option value="KIS">KIS</option>
          <option value="UPBit">UPBit</option>
        </select>
        
        <OrderBook broker={exchange} symbol={symbol} />
      </aside>

      {/* 중앙: 차트 */}
      <main className="w-full lg:w-auto flex">
        <ChartPlaceholder />
      </main>

      {/* 오른쪽: 거래 페어 선택 & 체결가격 */}
      <aside className="w-full lg:w-[300px] flex flex-col gap-2">
        <Pair broker={exchange} />
        <TradePrice broker={exchange} symbol={symbol} />
      </aside>
    </div>
  );
};

export default Trade;
