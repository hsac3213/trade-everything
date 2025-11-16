import React, { useState, useEffect } from 'react';
import { showToast } from '../Common/Toast';
import { SecureAuthService } from '../Auth/AuthService';
import { API_URL } from '../Common/Constants';

interface OrderProps {
  broker: string;
  symbol: string;
  selectedPrice?: number | null;
  onOrderSuccess?: () => void;
}

// --- 매수/매도 컨트롤 ---
const Order: React.FC<OrderProps> = ({ broker, symbol, selectedPrice, onOrderSuccess }) => {
  const [amount, setAmount] = useState<string>('');
  const [price, setPrice] = useState<string>('');
  const [orderType, setOrderType] = useState<'limit' | 'market'>('limit');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // selectedPrice가 변경되면 price 입력란에 반영
  useEffect(() => {
    if (selectedPrice !== null && selectedPrice !== undefined) {
      setPrice(selectedPrice.toString());
    }
  }, [selectedPrice]);

  // 주문 제출
  const handleOrder = async (side: 'BUY' | 'SELL') => {
    // 입력 검증
    if (!amount || parseFloat(amount) <= 0) {
      showToast.warning('Please enter a valid amount');
      return;
    }

    if (orderType === 'limit' && (!price || parseFloat(price) <= 0)) {
      showToast.warning('Please enter a valid price');
      return;
    }

    setIsSubmitting(true);

    try {
      const token = SecureAuthService.getAccessToken();
      const orderData = {
        symbol: symbol.toLowerCase(),
        side: side,
        quantity: parseFloat(amount),
        price: parseFloat(price),
      };

      const response = await fetch(`${API_URL}/place_order/${broker}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData),
      });

      const data = await response.json();

      if (data.message === 'success') {
        showToast.success(`${side} order placed successfully`);
        // 주문 성공 후 입력 필드 초기화
        setAmount('');
        if (orderType === 'market') {
          setPrice('');
        }
        // OpenOrder 목록 갱신
        if (onOrderSuccess) {
          onOrderSuccess();
        }
      } else {
        showToast.error(`Order failed: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error placing order:', error);
      showToast.error('Failed to place order');
    } finally {
      setIsSubmitting(false);
    }
  };

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
          <button
            onClick={() => handleOrder('BUY')}
            disabled={isSubmitting}
            className="w-full py-3 rounded-md bg-green-600 hover:bg-green-700 text-white font-bold text-lg transition-colors duration-200 disabled:bg-gray-600 disabled:cursor-not-allowed">
            {isSubmitting ? 'Processing...' : 'Buy'}
          </button>
          <button
            onClick={() => handleOrder('SELL')}
            disabled={isSubmitting}
            className="w-full py-3 rounded-md bg-red-600 hover:bg-red-700 text-white font-bold text-lg transition-colors duration-200 disabled:bg-gray-600 disabled:cursor-not-allowed">
            {isSubmitting ? 'Processing...' : 'Sell'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Order;
