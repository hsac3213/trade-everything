import React, { useState } from 'react';

// --- 매수/매도 컨트롤 ---
const Order: React.FC = () => {
  const [amount, setAmount] = useState<string>('');
  const [price, setPrice] = useState<string>('');

  const handlePriceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPrice(e.target.value);
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAmount(e.target.value);
  };

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-lg mt-4 lg:mt-0 h-[500px] flex flex-col">
      <h3 className="text-lg font-semibold mb-4 text-center text-gray-200">Order</h3>
      <div className="space-y-4 flex-1 flex flex-col justify-center">
        <div>
          <label htmlFor="price" className="block text-sm font-medium text-gray-400 mb-1">
            Order Price
          </label>
          <input
            type="number"
            id="price"
            value={price}
            onChange={handlePriceChange}
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
            value={amount}
            onChange={handleAmountChange}
            className="w-full p-2 rounded-md bg-gray-700 border border-gray-600 text-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="0.0000"
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
