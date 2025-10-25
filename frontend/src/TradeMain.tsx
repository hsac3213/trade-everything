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
  const [exchange, setExchange] = useState<string>('KIS');
  const [activeMenu, setActiveMenu] = useState<string>('Trade');

  // 메뉴별 컨텐츠 렌더링
  const renderContent = () => {
    switch (activeMenu) {
      case 'Trade':
        return (
          <div className="flex flex-col lg:flex-row gap-6">
            {/* 왼쪽: 호가창 */}
            <aside className="w-full lg:w-auto">
              <OrderBook />
            </aside>

            {/* 중앙: 차트 */}
            <main className="w-full lg:w-auto flex">
              <ChartPlaceholder />
            </main>

            {/* 오른쪽: 거래 페어 선택 */}
            <aside className="w-full lg:w-auto">
              <Pair />
            </aside>
          </div>
        );
      
      case 'Earn':
        return (
          <div className="bg-gray-800 rounded-lg p-8 shadow-lg">
            <h2 className="text-2xl font-bold mb-6">Earn</h2>
            <div className="space-y-6">
              <div className="bg-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4">Staking</h3>
                <p className="text-gray-300 mb-4">
                  Stake your crypto assets and earn rewards
                </p>
                <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors">
                  Start Staking
                </button>
              </div>
              
              <div className="bg-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4">Savings</h3>
                <p className="text-gray-300 mb-4">
                  Earn interest on your crypto holdings
                </p>
                <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors">
                  View Products
                </button>
              </div>
              
              <div className="bg-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4">Liquidity Mining</h3>
                <p className="text-gray-300 mb-4">
                  Provide liquidity and earn trading fees
                </p>
                <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors">
                  Explore Pools
                </button>
              </div>
            </div>
          </div>
        );
      
      case 'Assets':
        return (
          <div className="bg-gray-800 rounded-lg p-8 shadow-lg">
            <h2 className="text-2xl font-bold mb-6">My Assets</h2>
            <div className="space-y-4">
              {/* 총 자산 요약 */}
              <div className="bg-gray-700 rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-gray-400">Total Balance</span>
                  <span className="text-3xl font-bold">$0.00</span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-gray-400">Spot</div>
                    <div className="text-lg font-semibold">$0.00</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Earning</div>
                    <div className="text-lg font-semibold">$0.00</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Funding</div>
                    <div className="text-lg font-semibold">$0.00</div>
                  </div>
                </div>
              </div>
              
              {/* 자산 목록 테이블 */}
              <div className="bg-gray-700 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-600">
                    <tr>
                      <th className="px-6 py-3 text-left text-sm font-semibold">Asset</th>
                      <th className="px-6 py-3 text-right text-sm font-semibold">Total</th>
                      <th className="px-6 py-3 text-right text-sm font-semibold">Available</th>
                      <th className="px-6 py-3 text-right text-sm font-semibold">In Order</th>
                      <th className="px-6 py-3 text-right text-sm font-semibold">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-t border-gray-600">
                      <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                        No assets to display
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              {/* 액션 버튼 */}
              <div className="flex gap-4">
                <button className="flex-1 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-md transition-colors font-medium">
                  Deposit
                </button>
                <button className="flex-1 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-md transition-colors font-medium">
                  Withdraw
                </button>
                <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md transition-colors font-medium">
                  Transfer
                </button>
              </div>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4 lg:p-8 font-sans">
      <div className="flex gap-6">
        {/* 좌측: 로고 + 거래소 선택 (세로 배치) */}
        <div className="flex flex-col gap-3">
          <h1 className="text-3xl font-bold text-gray-100 h-[36px] flex items-center">
            Trade Everything
          </h1>
          
          {/* Trade 메뉴일 때만 거래소 선택 콤보박스 표시 */}
          {activeMenu === 'Trade' && (
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
          )}
        </div>

        {/* 우측 영역 */}
        <div className="flex flex-col gap-3 flex-1">
          {/* 메뉴 탭 - Trade Everything 로고와 같은 높이 */}
          <div className="flex gap-1 h-[36px]">
            {['Trade', 'Earn', 'Assets'].map((menu) => (
              <button
                key={menu}
                onClick={() => setActiveMenu(menu)}
                className={`px-4 h-full text-sm font-medium rounded transition-colors ${
                  activeMenu === menu
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                }`}
              >
                {menu}
              </button>
            ))}
          </div>
          
          {/* 메인 레이아웃 - 메뉴별 컨텐츠 */}
          {renderContent()}
        </div>
      </div>
    </div>
  );
}

export default TradeMain;
