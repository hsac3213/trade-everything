import React, { useState, useEffect } from 'react';

interface TradingPair {
  symbol: string;
  display_name: string;
  price: string;
  change: string;
  positive: boolean;
  uniqueKey: string; // 고유 키 추가
}

interface PairProps {
  broker?: string;
}

// --- 거래 페어 선택 컴포넌트 ---
const Pair: React.FC<PairProps> = ({ broker = 'Binance' }) => {
  const [selectedPair, setSelectedPair] = useState<string>('BTC/USDT');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [modalSearchTerm, setModalSearchTerm] = useState<string>('');
  const [allSymbols, setAllSymbols] = useState<TradingPair[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [favorites, setFavorites] = useState<Set<string>>(new Set()); // 즐겨찾기 상태

  console.log('Pair component - broker prop:', broker);

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

  const modalFilteredPairs = allSymbols.filter(pair => 
    pair.symbol.toLowerCase().includes(modalSearchTerm.toLowerCase())
  );
  
  // 즐겨찾기 토글 핸들러
  const toggleFavorite = (symbol: string, event: React.MouseEvent) => {
    event.stopPropagation(); // 페어 선택 이벤트 방지
    setFavorites(prev => {
      const newFavorites = new Set(prev);
      if (newFavorites.has(symbol)) {
        newFavorites.delete(symbol);
        console.log(`⭐ Removed from favorites: ${symbol}`);
      } else {
        newFavorites.add(symbol);
        console.log(`⭐ Added to favorites: ${symbol}`);
      }
      return newFavorites;
    });
  };

    // 모달이 열릴 때 심볼 목록 가져오기
  useEffect(() => {
    if (isModalOpen) {
      console.log('Fetching symbols for broker:', broker);
      fetchSymbols(broker);
    }
  }, [isModalOpen, broker]);

  const fetchSymbols = async (selectedBroker: string) => {
    console.log('fetchSymbols called with:', selectedBroker);
    setIsLoading(true);
    setAllSymbols([]); // 기존 목록 초기화
    try {
      const url = `http://localhost:8001/symbols/${selectedBroker}`;
      console.log('Fetching from URL:', url);
      const response = await fetch(url);
      const data = await response.json();
      console.log('API Response:', data);
      
      if (data.message === 'success' && data.symbols && Array.isArray(data.symbols)) {
        // 심볼을 표시 형식으로 변환 (더미 가격/등락률 추가)
        const formattedSymbols: TradingPair[] = data.symbols.map((s: any) => {
          // 더미 가격과 등락률 생성
          const dummyPrice = (Math.random() * 10000).toFixed(2);
          const dummyChange = ((Math.random() - 0.5) * 10).toFixed(2);
          const isPositive = parseFloat(dummyChange) >= 0;
          
          return {
            symbol: s.symbol,
            display_name: s.display_name,
            price: dummyPrice,
            change: `${isPositive ? '+' : ''}${dummyChange}%`,
            positive: isPositive,
            uniqueKey: s.symbol // 고유한 심볼 코드를 키로 사용
          };
        });
        
        setAllSymbols(formattedSymbols);
      } else {
        console.error('Invalid response format:', data);
      }
    } catch (error) {
      console.error('Failed to fetch symbols:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePairSelect = (symbol: string) => {
    setSelectedPair(symbol);
    setIsModalOpen(false);
    setModalSearchTerm('');
  };

  return (
    <div className="bg-gray-800 rounded-lg p-3 flex flex-col shadow-lg h-[520px]">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-base font-semibold text-gray-200">Pair</h3>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="px-3 py-1 text-xs font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-md transition-colors"
        >
          More
        </button>
      </div>
      
      {/* 검색 입력 */}
      <input
        type="text"
        placeholder="Search Pairs..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="mb-2 p-2 rounded-md bg-gray-800 border border-gray-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      
      {/* 페어 목록 */}
      <div className="flex-1 overflow-y-auto space-y-1 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800 hover:scrollbar-thumb-gray-500">
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

      {/* 모달 */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setIsModalOpen(false)}>
          <div className="bg-gray-800 rounded-lg p-6 w-[600px] max-h-[80vh] flex flex-col shadow-2xl" onClick={(e) => e.stopPropagation()}>
            {/* 모달 헤더 */}
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-200">Search Pairs</h2>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-md transition-colors"
              >
                Close
              </button>
            </div>

            {/* 검색 입력 */}
            <input
              type="text"
              placeholder="Search pairs..."
              value={modalSearchTerm}
              onChange={(e) => setModalSearchTerm(e.target.value)}
              className="mb-4 p-3 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />

            {/* 페어 목록 */}
            <div className="flex-1 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
              {isLoading ? (
                <div className="text-center text-gray-400 py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="mt-2">Loading symbols...</p>
                </div>
              ) : modalFilteredPairs.length > 0 ? (
                modalFilteredPairs.map((pair) => (
                  <div
                    key={pair.uniqueKey}
                    onClick={() => handlePairSelect(pair.symbol)}
                    className={`p-4 rounded-md cursor-pointer transition-colors ${
                      selectedPair === pair.symbol
                        ? 'bg-blue-600 hover:bg-blue-700'
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {/* 별 모양 버튼 */}
                      <button
                        onClick={(e) => toggleFavorite(pair.symbol, e)}
                        className={`flex-shrink-0 p-1 rounded transition-colors ${
                          favorites.has(pair.symbol)
                            ? 'text-yellow-400 hover:text-yellow-500'
                            : 'text-gray-500 hover:text-yellow-400'
                        }`}
                        title={favorites.has(pair.symbol) ? 'Remove from favorites' : 'Add to favorites'}
                      >
                        {favorites.has(pair.symbol) ? (
                          // 채워진 별
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        ) : (
                          // 빈 별
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                          </svg>
                        )}
                      </button>
                      
                      {/* 심볼 정보 */}
                      <div className="flex-1">
                        <div className="flex justify-between items-center">
                          <span className="font-semibold text-base">{pair.display_name}({pair.symbol})</span>
                          <span className={`text-sm font-medium ${pair.positive ? 'text-green-400' : 'text-red-400'}`}>
                            {pair.change}
                          </span>
                        </div>
                        <div className="text-sm text-gray-300 mt-1">
                          ${pair.price}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-400 py-8">
                  No pairs found
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Pair;
