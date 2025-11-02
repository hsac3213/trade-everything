import React, { useState } from 'react';

// --- 매수/매도 컨트롤 ---
const Order: React.FC = () => {
  const [amount, setAmount] = useState<string>('');
  const [price, setPrice] = useState<string>('');
  const [orderType, setOrderType] = useState<'limit' | 'market'>('limit');

  const handlePriceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // 빈 문자열이거나 0 이상의 숫자만 허용
    if (value === '' || (parseFloat(value) >= 0 && !isNaN(parseFloat(value)))) {
      setPrice(value);
    }
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // 빈 문자열이거나 0 이상의 숫자만 허용
    if (value === '' || (parseFloat(value) >= 0 && !isNaN(parseFloat(value)))) {
      setAmount(value);
    }
  };
  
  // 마이너스, e, E, + 키 입력 방지
  const preventInvalidKeys = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === '-' || e.key === 'e' || e.key === 'E' || e.key === '+') {
      e.preventDefault();
    }
  };

  return (
    <div className="flex-1 bg-gray-900 p-3 rounded-lg shadow-lg mt-4 lg:mt-0 flex flex-col">
      <div className="flex justify-between items-center mb-2">
        <div className="flex gap-2">
          <button
            onClick={() => setOrderType('limit')}
            className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
              orderType === 'limit'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            Limit
          </button>
          <button
            onClick={() => setOrderType('market')}
            className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
              orderType === 'market'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            Market
          </button>
        </div>
      </div>
      <div className="space-y-3">
        <div>
          <label htmlFor="price" className="block text-sm font-medium text-gray-400 mb-1">
            Order Price
          </label>
          <input
            type="number"
            id="price"
            min="0"
            step="0.01"
            value={price}
            onChange={handlePriceChange}
            onKeyDown={preventInvalidKeys}
            className="w-full p-2 rounded-md bg-gray-700 border border-gray-600 text-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="0"
          />
        </div>
        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-gray-400 mb-1">
            Order Amount
          </label>
          <input
            type="number"
            id="amount"
            min="0"
            step="0.01"
            value={amount}
            onChange={handleAmountChange}
            onKeyDown={preventInvalidKeys}
            className="w-full p-2 rounded-md bg-gray-700 border border-gray-600 text-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="0"
          />
        </div>
        
        {/* 총 주문 금액 (간단 계산) */}
        <div className="text-center text-gray-400 text-sm">
          <p>Total Order Price</p>
          <p className="text-lg text-white font-mono">
            {((Number(price) || 0) * (Number(amount) || 0)).toLocaleString(undefined, { maximumFractionDigits: 0 })} KRW
          </p>
        </div>

        <div className="flex gap-4">
          <button className="w-full py-3 rounded-md bg-green-600 hover:bg-green-700 text-white font-bold text-lg transition-colors duration-200">
            Buy
          </button>
          <button className="w-full py-3 rounded-md bg-red-600 hover:bg-red-700 text-white font-bold text-lg transition-colors duration-200">
            Sell
          </button>
        </div>
      </div>
    </div>
  );
};

export default Order;
