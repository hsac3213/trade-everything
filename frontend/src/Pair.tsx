import React, { useState, useEffect } from 'react';
import { SecureAuthService } from './AuthService';

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
  const [favoritePairs, setFavoritePairs] = useState<TradingPair[]>([]); // 즐겨찾기 페어 목록

  // 즐겨찾기 목록 로드
  useEffect(() => {
    loadFavorites();
  }, [broker]);

  const loadFavorites = async () => {
    try {
      const token = SecureAuthService.getAccessToken();
      if (!token) {
        // 로그인하지 않은 경우 기본 목록 표시
        setFavoritePairs([
          { symbol: 'BTCUSDT', display_name: 'BTC/USDT', price: '43,250.00', change: '+2.45%', positive: true, uniqueKey: 'BTCUSDT' },
          { symbol: 'ETHUSDT', display_name: 'ETH/USDT', price: '2,280.50', change: '+1.85%', positive: true, uniqueKey: 'ETHUSDT' },
          { symbol: 'BNBUSDT', display_name: 'BNB/USDT', price: '315.20', change: '-0.52%', positive: false, uniqueKey: 'BNBUSDT' },
          { symbol: 'SOLUSDT', display_name: 'SOL/USDT', price: '98.75', change: '+5.12%', positive: true, uniqueKey: 'SOLUSDT' },
        ]);
        return;
      }

      const url = broker 
        ? `http://localhost:8001/api/favorites/list?broker=${encodeURIComponent(broker)}`
        : 'http://localhost:8001/api/favorites/list';
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        const favoriteSymbols = new Set<string>(data.map((item: any) => item.symbol));
        setFavorites(favoriteSymbols);
        
        // 즐겨찾기 목록을 TradingPair 형식으로 변환
        const favoritePairsList: TradingPair[] = data.map((item: any) => {
          // 더미 가격과 등락률 생성
          const dummyPrice = (Math.random() * 10000).toFixed(2);
          const dummyChange = ((Math.random() - 0.5) * 10).toFixed(2);
          const isPositive = parseFloat(dummyChange) >= 0;
          
          return {
            symbol: item.symbol,
            display_name: item.display_name || item.symbol,
            price: dummyPrice,
            change: `${isPositive ? '+' : ''}${dummyChange}%`,
            positive: isPositive,
            uniqueKey: item.symbol
          };
        });
        
        setFavoritePairs(favoritePairsList);
      } else {
        // 에러 시 기본 목록 표시
        setFavoritePairs([
          { symbol: 'BTCUSDT', display_name: 'BTC/USDT', price: '43,250.00', change: '+2.45%', positive: true, uniqueKey: 'BTCUSDT' },
          { symbol: 'ETHUSDT', display_name: 'ETH/USDT', price: '2,280.50', change: '+1.85%', positive: true, uniqueKey: 'ETHUSDT' },
        ]);
      }
    } catch (error) {
      console.error('Failed to load favorites:', error);
      // 에러 시 기본 목록 표시
      setFavoritePairs([
        { symbol: 'BTCUSDT', display_name: 'BTC/USDT', price: '43,250.00', change: '+2.45%', positive: true, uniqueKey: 'BTCUSDT' },
        { symbol: 'ETHUSDT', display_name: 'ETH/USDT', price: '2,280.50', change: '+1.85%', positive: true, uniqueKey: 'ETHUSDT' },
      ]);
    }
  };

  const filteredPairs = favoritePairs.filter(pair => 
    pair.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const modalFilteredPairs = allSymbols.filter(pair => 
    pair.symbol.toLowerCase().includes(modalSearchTerm.toLowerCase())
  );
  
  // 즐겨찾기 토글 핸들러
  const toggleFavorite = async (symbol: string, displayName: string, event: React.MouseEvent) => {
    event.stopPropagation(); // 페어 선택 이벤트 방지
    
    const token = SecureAuthService.getAccessToken();
    if (!token) {
      alert('Please login to use favorites feature');
      return;
    }

    const isFavorite = favorites.has(symbol);
    
    try {
      if (isFavorite) {
        // 즐겨찾기 제거
        const response = await fetch(
          `http://localhost:8001/api/favorites/remove?broker=${encodeURIComponent(broker)}&symbol=${encodeURIComponent(symbol)}`,
          {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );

        if (response.ok) {
          setFavorites(prev => {
            const newFavorites = new Set(prev);
            newFavorites.delete(symbol);
            return newFavorites;
          });
          // 즐겨찾기 목록 새로고침
          loadFavorites();
        } else if (response.status === 401) {
          alert('Session expired - please login again');
        }
      } else {
        // 즐겨찾기 추가
        const response = await fetch('http://localhost:8001/api/favorites/add', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            broker,
            symbol,
            display_name: displayName
          })
        });

        if (response.ok) {
          setFavorites(prev => {
            const newFavorites = new Set(prev);
            newFavorites.add(symbol);
            return newFavorites;
          });
          // 즐겨찾기 목록 새로고침
          loadFavorites();
        } else if (response.status === 401) {
          alert('Session expired - please login again');
        }
      }
    } catch (error) {
      console.error('Network error:', error);
      alert('Failed to update favorites. Please check your connection.');
    }
  };

    // 모달이 열릴 때 심볼 목록 가져오기
  useEffect(() => {
    if (isModalOpen) {
      fetchSymbols(broker);
    }
  }, [isModalOpen, broker]);

  const fetchSymbols = async (selectedBroker: string) => {
    setIsLoading(true);
    setAllSymbols([]); // 기존 목록 초기화
    try {
      const url = `http://localhost:8001/symbols/${selectedBroker}`;
      const response = await fetch(url);
      const data = await response.json();
      
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
                        onClick={(e) => toggleFavorite(pair.symbol, pair.display_name, e)}
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
