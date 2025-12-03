import React, { useEffect, useState } from 'react';
import { SecureAuthService } from './Auth/AuthService';
import { API_URL } from './Common/Constants';

interface Asset {
  broker: string;
  type: string;
  display_name: string;
  symbol: string;
  amount: number;
}

const Assets: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const token = SecureAuthService.getAccessToken();
        if (!token) {
          setError("No access token found");
          setLoading(false);
          return;
        }

        const response = await fetch(`${API_URL}/assets`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch assets');
        }

        const data = await response.json();
        if (data.message === 'success') {
          setAssets(data.assets);
        } else {
          setError(data.error || 'Unknown error');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchAssets();
  }, []);

  if (loading) return <div className="text-white p-8">Loading assets...</div>;
  if (error) return <div className="text-red-500 p-8">Error: {error}</div>;

  return (
    <div className="bg-gray-800 rounded-lg p-8 shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-white">My Assets</h2>
      <div className="space-y-4">
        {/* 자산 목록 테이블 */}
        <div className="bg-gray-700 rounded-lg overflow-hidden">
          <table className="w-full text-white">
            <thead className="bg-gray-600">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold">Broker</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Type</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Name</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Symbol</th>
                <th className="px-6 py-3 text-right text-sm font-semibold">Amount</th>
              </tr>
            </thead>
            <tbody>
              {(
                assets.map((asset, index) => (
                  <tr key={index} className="border-t border-gray-600 hover:bg-gray-600 transition-colors">
                    <td className="px-6 py-4 text-sm capitalize">{asset.broker}</td>
                    <td className="px-6 py-4 text-sm capitalize">{asset.type}</td>
                    <td className="px-6 py-4 text-sm">{asset.display_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-400">{asset.symbol}</td>
                    {/*<td className="px-6 py-4 text-sm text-right font-mono">{asset.amount.toLocaleString()}</td>*/}
                    <td className="px-6 py-4 text-sm text-right font-mono">*</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Assets;
