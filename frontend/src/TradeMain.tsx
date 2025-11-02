import React, { useState } from 'react';
import SimpleChart from './CandleChart';
import OrderBook from './OrderBook';
import Order from './Order';
import Pair from './Pair';
import OpenOrder from './OpenOrder';
import TradePrice from './TradePrice';
import Earn from './Earn';
import Assets from './Assets';

// --- 차트 플레이스홀더 ---
interface ChartPlaceholderProps {
  broker: string;
  symbol: string;
}

const ChartPlaceholder: React.FC<ChartPlaceholderProps> = ({ broker, symbol }) => {
  const [timeframe, setTimeframe] = useState<string>('1D');
  
  const timeframes = [
    { value: 'Tick', label: 'Tick' },
    { value: '1S', label: '1S' },
    { value: '1M', label: '1M' },
    { value: '1H', label: '1H' },
    { value: '1D', label: '1D' },
  ];
  
  // broker나 symbol이 변경되면 로그 출력
  console.log(`📊 ChartPlaceholder rendering with broker: ${broker}, symbol: ${symbol}`);

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
        <SimpleChart 
          key={`candle-${broker}-${symbol}`}
          height={460} 
          width="1300px" 
          broker={broker}
          symbol={symbol}
        />
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

interface TradeMainProps {
  onLogout?: () => void;
}

// --- 메인 거래 컴포넌트 ---
const TradeMain: React.FC<TradeMainProps> = ({ onLogout }) => {
  const [exchange, setExchange] = useState<string>('Binance');
  const [activeMenu, setActiveMenu] = useState<string>('Trade');
  const [symbol, setSymbol] = useState<string>('btcusdt');
  
  // 거래소 변경 핸들러
  const handleExchangeChange = (newExchange: string) => {
    console.log(`🔄 Changing exchange from ${exchange} to ${newExchange}`);
    
    // 1. 거래소 변경
    setExchange(newExchange);
    
    // 2. 심볼 초기화 (각 거래소의 기본 심볼로)
    const defaultSymbol = getDefaultSymbol(newExchange);
    setSymbol(defaultSymbol);
    
    console.log(`✅ Exchange changed to ${newExchange}, symbol reset to ${defaultSymbol}`);
  };
  
  // 거래소별 기본 심볼 반환
  const getDefaultSymbol = (exchangeName: string): string => {
    switch (exchangeName) {
      case 'Binance':
      case 'UPBit':
        return 'btcusdt';
      case 'KIS':
        return '005930'; // 삼성전자
      default:
        return 'btcusdt';
    }
  };

  // 메뉴별 컨텐츠 렌더링
  const renderContent = () => {
    switch (activeMenu) {
      case 'Trade':
        return (
          <>
            {/* 로고 + 메뉴 탭 */}
            <div className="flex items-center gap-6">
              <h1 className="text-3xl font-bold text-gray-100">
                Trade Everything
              </h1>
              <div className="flex gap-1">
                {['Trade', 'Earn', 'Assets'].map((menu) => (
                  <button
                    key={menu}
                    onClick={() => setActiveMenu(menu)}
                    className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                      activeMenu === menu
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    {menu}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex flex-col lg:flex-row gap-6">
              {/* 왼쪽: 거래소 선택 + 호가창 */}
              <aside className="w-full lg:w-[300px] flex flex-col gap-3">
                {/* 거래소 선택 콤보박스 */}
                <select
                  id="exchange-select"
                  value={exchange}
                  onChange={(e) => handleExchangeChange(e.target.value)}
                  className="bg-gray-800 text-white border border-gray-600 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
                >
                  <option value="Binance">Binance</option>
                  <option value="KIS">KIS</option>
                  <option value="UPBit">UPBit</option>
                </select>
                
                <OrderBook broker={exchange} symbol={symbol} key={`orderbook-${exchange}-${symbol}`} />
              </aside>

              {/* 중앙: 차트 */}
              <main className="w-full lg:w-auto flex">
                <ChartPlaceholder 
                  broker={exchange} 
                  symbol={symbol}
                  key={`chart-${exchange}-${symbol}`} 
                />
              </main>

              {/* 오른쪽: 거래 페어 선택 & 체결가격 */}
              <aside className="w-full lg:w-[300px] flex flex-col gap-2">
                <Pair broker={exchange} key={`pair-${exchange}`} />
                <TradePrice broker={exchange} symbol={symbol} key={`tradeprice-${exchange}-${symbol}`} />
              </aside>
            </div>
          </>
        );
      
      case 'Earn':
        return (
          <>
            {/* 로고 + 메뉴 탭 */}
            <div className="flex items-center gap-6">
              <h1 className="text-3xl font-bold text-gray-100">
                Trade Everything
              </h1>
              <div className="flex gap-1">
                {['Trade', 'Earn', 'Assets'].map((menu) => (
                  <button
                    key={menu}
                    onClick={() => setActiveMenu(menu)}
                    className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                      activeMenu === menu
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    {menu}
                  </button>
                ))}
              </div>
            </div>
            
            <Earn />
          </>
        );
      
      case 'Assets':
        return (
          <>
            {/* 로고 + 메뉴 탭 */}
            <div className="flex items-center gap-6">
              <h1 className="text-3xl font-bold text-gray-100">
                Trade Everything
              </h1>
              <div className="flex gap-1">
                {['Trade', 'Earn', 'Assets'].map((menu) => (
                  <button
                    key={menu}
                    onClick={() => setActiveMenu(menu)}
                    className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                      activeMenu === menu
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    {menu}
                  </button>
                ))}
              </div>
            </div>
            
            <Assets />
          </>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4 lg:p-8 font-sans">
      <div className="flex flex-col gap-3 flex-1">
        {/* 메인 레이아웃 - 메뉴별 컨텐츠 */}
        {renderContent()}
      </div>
    </div>
  );
}

export default TradeMain;
