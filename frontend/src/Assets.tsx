import React from 'react';

const Assets: React.FC = () => {
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
      </div>
    </div>
  );
};

export default Assets;
