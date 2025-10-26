import React from 'react';

const Earn: React.FC = () => {
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
};

export default Earn;
