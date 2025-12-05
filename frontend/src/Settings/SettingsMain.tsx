import React, { useState, useEffect } from 'react';
import SecureAuthService from '../Auth/AuthService';
import { API_URL } from '../Common/Constants';
import PasskeyManager from '../Auth/PasskeyManager';

interface APIKey {
  apikey_name: string;
  masked_value: string;
  has_value: boolean;
}

interface BrokerAPIKeys {
  broker_name: string;
  apikeys: APIKey[];
}

const SettingsMain: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'apikeys' | 'passkeys'>('apikeys');
  const [brokerTokens, setBrokerAPIKeys] = useState<BrokerAPIKeys[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  
  // API Key 추가/수정 폼 상태
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    broker_name: 'Binance',
    apikey_name: 'API',
    apikey: ''
  });

  useEffect(() => {
    loadAPIKeys();
  }, []);

  const loadAPIKeys = async () => {
    setLoading(true);
    setError('');
    
    try {
      const token = SecureAuthService.getAccessToken();
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/api/apikeys/list`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load apikeys');
      }

      const data = await response.json();
      setBrokerAPIKeys(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load apikeys');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAPIKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const token = SecureAuthService.getAccessToken();
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`${API_URL}/api/apikeys/add`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save API Key');
      }

      setMessage('✅ API Key saved successfully!');
      setShowAddForm(false);
      setFormData({ broker_name: 'Binance', apikey_name: 'API', apikey: '' });
      await loadAPIKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save API Key');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAPIKey = async (brokerName: string, apikeyName: string) => {
    if (!window.confirm(`Are you sure you want to delete ${brokerName} ${apikeyName}?`)) {
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    try {
      const token = SecureAuthService.getAccessToken();
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(
        `${API_URL}/api/apikeys/delete/${encodeURIComponent(brokerName)}/${encodeURIComponent(apikeyName)}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete token');
      }

      setMessage('API Key deleted successfully');
      await loadAPIKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete API Key');
    } finally {
      setLoading(false);
    }
  };

  const renderAPIKeysTab = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold text-white">API API Keys</h3>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          disabled={loading}
          className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-md transition-colors"
        >
          {showAddForm ? '✖️ Cancel' : '➕ Add Token'}
        </button>
      </div>

      {showAddForm && (
        <div className="bg-gray-700 rounded-lg p-6">
          <h4 className="text-lg font-medium text-white mb-4">Add/Update API Key</h4>
          <form onSubmit={handleAddAPIKey} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Broker
              </label>
              <select
                value={formData.broker_name}
                onChange={(e) => setFormData({ ...formData, broker_name: e.target.value })}
                className="w-full bg-gray-600 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Binance">Binance</option>
                <option value="KIS">KIS</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                API Key Name
              </label>
              <select
                value={formData.apikey_name}
                onChange={(e) => setFormData({ ...formData, apikey_name: e.target.value })}
                className="w-full bg-gray-600 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {formData.broker_name === 'Binance' ? (
                  <>
                    <option value="API">API Key</option>
                    <option value="Private">Private Key</option>
                  </>
                ) : (
                  <>
                    <option value="APP">APP Key</option>
                    <option value="SEC">Secret Key</option>
                    <option value="ACCOUNT_NUMBER_0">Account Number (Part 1)</option>
                    <option value="ACCOUNT_NUMBER_1">Account Number (Part 2)</option>
                    <option value="HTS_ID">HTS ID</option>
                  </>
                )}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Token Value
              </label>
              <textarea
                value={formData.apikey}
                onChange={(e) => setFormData({ ...formData, apikey: e.target.value })}
                placeholder="Enter your token here..."
                className="w-full bg-gray-600 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                rows={4}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-md transition-colors"
            >
              {loading ? 'Saving...' : 'Save Token'}
            </button>
          </form>
        </div>
      )}

      {loading && brokerTokens.length === 0 ? (
        <div className="text-gray-400 text-center py-8">Loading...</div>
      ) : brokerTokens.length === 0 ? (
        <div className="text-gray-400 text-center py-8">No API Keys configured</div>
      ) : (
        brokerTokens.map((broker) => (
          <div key={broker.broker_name} className="bg-gray-700 rounded-lg p-6">
            <h4 className="text-lg font-semibold text-white mb-4">{broker.broker_name}</h4>
            <div className="space-y-3">
              {broker.apikeys.map((apikey, index) => (
                <div
                  key={index}
                  className="flex justify-between items-center bg-gray-600 px-4 py-3 rounded-md"
                >
                  <div className="flex-1">
                    <div className="text-white font-medium mb-1">{apikey.apikey_name}</div>
                    <div className="text-sm text-gray-400 font-mono">
                      {apikey.has_value ? apikey.masked_value : 'Not set'}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteAPIKey(broker.broker_name, apikey.apikey_name)}
                    disabled={loading}
                    className="bg-red-600 hover:bg-red-700 disabled:bg-gray-700 text-white px-3 py-2 rounded-md transition-colors ml-4"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );

  return (
    <div className="bg-gray-800 rounded-lg p-8 shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-white">Settings</h2>

      <div className="flex gap-6">
        {/* 좌측 사이드바 메뉴 */}
        <div className="w-64 flex-shrink-0">
          <nav className="space-y-2">
            <button
              onClick={() => setActiveTab('apikeys')}
              className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${
                activeTab === 'apikeys'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700'
              }`}
            >
              🔑 API Keys
            </button>
            <button
              onClick={() => setActiveTab('passkeys')}
              className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-colors ${
                activeTab === 'passkeys'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700'
              }`}
            >
              🔐 Passkeys
            </button>
          </nav>
        </div>

        {/* 우측 컨텐츠 영역 */}
        <div className="flex-1">
          {/* 알림 메시지 */}
          {message && (
            <div className="bg-green-900/50 border border-green-500 text-green-200 px-4 py-3 rounded-md mb-4">
              {message}
            </div>
          )}

          {error && (
            <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-md mb-4">
              {error}
            </div>
          )}

          {/* 탭 컨텐츠 */}
          {activeTab === 'apikeys' ? renderAPIKeysTab() : <PasskeyManager />}
        </div>
      </div>
    </div>
  );
};

export default SettingsMain;
