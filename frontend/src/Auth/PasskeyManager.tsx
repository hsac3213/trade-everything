import React, { useState, useEffect } from 'react';
import SecureAuthService from './AuthService';
import { API_URL } from '../common/constants';

interface Passkey {
  credential_id: string;
  created_at: string | null;
  last_used: string | null;
  sign_count: number;
}

const PasskeyManager: React.FC = () => {
  const [passkeys, setPasskeys] = useState<Passkey[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [username, setUsername] = useState('');

  useEffect(() => {
    loadPasskeys();
    loadUsername();
  }, []);

  const loadUsername = async () => {
    try {
      const user = await SecureAuthService.getMe();
      setUsername(user.username);
    } catch (err) {
      console.error('Failed to load username:', err);
    }
  };

  const loadPasskeys = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/auth/passkey/list`, {
        headers: SecureAuthService.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to load passkeys');
      }

      const data = await response.json();
      setPasskeys(data.passkeys);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load passkeys');
    } finally {
      setLoading(false);
    }
  };

  const addPasskey = async () => {
    setLoading(true);
    setError('');
    setMessage('');

    try {
      if (!username) {
        throw new Error('Username not found');
      }

      // 1. 등록 시작
      const beginResponse = await fetch(`${API_URL}/auth/passkey/add/begin`, {
        method: 'POST',
        headers: SecureAuthService.getAuthHeaders(),
        body: JSON.stringify({ username }),
      });

      if (!beginResponse.ok) {
        const error = await beginResponse.json();
        throw new Error(error.detail || 'Failed to start registration');
      }

      const options = await beginResponse.json();

      // 2. WebAuthn으로 credential 생성
      const { startRegistration } = await import('@simplewebauthn/browser');
      const attResp = await startRegistration(options);

      // 3. 등록 완료
      const completeResponse = await fetch(`${API_URL}/auth/passkey/add/complete`, {
        method: 'POST',
        headers: SecureAuthService.getAuthHeaders(),
        body: JSON.stringify({
          username,
          attestationResponse: attResp,
        }),
      });

      if (!completeResponse.ok) {
        const error = await completeResponse.json();
        throw new Error(error.detail || 'Registration failed');
      }

      setMessage('✅ New passkey added successfully!');
      await loadPasskeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add passkey');
    } finally {
      setLoading(false);
    }
  };

  const removePasskey = async (credentialId: string) => {
    if (!window.confirm('Are you sure you want to remove this passkey?')) {
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await fetch(
        `${API_URL}/auth/passkey/remove/${encodeURIComponent(credentialId)}`,
        {
          method: 'DELETE',
          headers: SecureAuthService.getAuthHeaders(),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to remove passkey');
      }

      setMessage('🗑️ Passkey removed successfully');
      await loadPasskeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove passkey');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-white">Passkey Management</h2>
        <button
          onClick={addPasskey}
          disabled={loading}
          className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-md transition-colors"
        >
          {loading ? 'Adding...' : '➕ Add Passkey'}
        </button>
      </div>

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

      <div className="space-y-4">
        {loading && passkeys.length === 0 ? (
          <div className="text-gray-400 text-center py-8">Loading...</div>
        ) : passkeys.length === 0 ? (
          <div className="text-gray-400 text-center py-8">No passkeys registered</div>
        ) : (
          passkeys.map((passkey, index) => (
            <div
              key={index}
              className="bg-gray-700 rounded-lg p-4 flex justify-between items-center"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-white font-medium">🔑 Passkey {index + 1}</span>
                  <span className="text-xs text-gray-400 font-mono bg-gray-600 px-2 py-1 rounded">
                    {passkey.credential_id}
                  </span>
                </div>
                <div className="text-sm text-gray-400 space-y-1">
                  <div>Created: {formatDate(passkey.created_at)}</div>
                  <div>Last used: {formatDate(passkey.last_used)}</div>
                  <div>Sign count: {passkey.sign_count}</div>
                </div>
              </div>
              <button
                onClick={() => removePasskey(passkey.credential_id)}
                disabled={loading || passkeys.length === 1}
                className="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-md transition-colors ml-4"
                title={passkeys.length === 1 ? 'Cannot remove last passkey' : 'Remove passkey'}
              >
                🗑️ Remove
              </button>
            </div>
          ))
        )}
      </div>

      <div className="mt-6 text-sm text-gray-400">
        <p>💡 Tip: You can register multiple passkeys for different devices.</p>
        <p className="mt-1">Each device (phone, laptop, security key) can have its own passkey.</p>
      </div>
    </div>
  );
};

export default PasskeyManager;
