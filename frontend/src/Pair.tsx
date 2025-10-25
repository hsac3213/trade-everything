import React, { useState } from 'react';

// --- 거래 페어 선택 컴포넌트 ---
const Pair: React.FC = () => {
  const [selectedPair, setSelectedPair] = useState<string>('BTC/USDT');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const tradingPairs = [
    { symbol: 'BTC/USDT', price: '43,250.00', change: '+2.45%', positive: true },
    { symbol: 'ETH/USDT', price: '2,280.50', change: '+1.85%', positive: true },
    { symbol: 'BNB/USDT', price: '315.20', change: '-0.52%', positive: false },
    { symbol: 'SOL/USDT', price: '98.75', change: '+5.12%', positive: true },
    { symbol: 'XRP/USDT', price: '0.6234', change: '-1.23%', positive: false },
    { symbol: 'ADA/USDT', price: '0.4512', change: '+0.89%', positive: true },
    { symbol: 'DOGE/USDT', price: '0.0825', change: '+3.21%', positive: true },
    { symbol: 'AVAX/USDT', price: '36.45', change: '-2.15%', positive: false },
  ];

  const filteredPairs = tradingPairs.filter(pair => 
    pair.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bg-gray-800 rounded-lg p-4 flex flex-col shadow-lg h-[515px]">
      <h3 className="text-lg font-semibold mb-3 text-gray-200">Pair</h3>
      
      {/* 검색 입력 */}
      <input
        type="text"
        placeholder="Search Pairs..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="mb-3 p-2 rounded-md bg-gray-800 border border-gray-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      
      {/* 페어 목록 */}
      <div className="flex-1 overflow-y-auto space-y-1">
        {filteredPairs.map((pair) => (
          <div
            key={pair.symbol}
            onClick={() => setSelectedPair(pair.symbol)}
            className={`p-3 rounded-md cursor-pointer transition-colors ${
              selectedPair === pair.symbol
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-800 hover:bg-gray-700'
            }`}
          >
            <div className="flex justify-between items-center">
              <span className="font-semibold text-sm">{pair.symbol}</span>
              <span className={`text-sm font-medium ${pair.positive ? 'text-green-400' : 'text-red-400'}`}>
                {pair.change}
              </span>
            </div>
            <div className="text-xs text-gray-400 mt-1">
              ${pair.price}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Pair;
