import React, { useState, useEffect } from 'react';
import SecureAuthService from './AuthService';

interface LoginProps {
  onLoginSuccess: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  // localStorage에서 저장된 username 불러오기
  const [username, setUsername] = useState(() => {
    return localStorage.getItem('trade_username') || '';
  });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // username이 변경될 때마다 localStorage에 저장
  useEffect(() => {
    if (username) {
      localStorage.setItem('trade_username', username);
    }
  }, [username]);

  const onLoginClick = async () => {
    setError('');
    setMessage('');
    setIsLoading(true);

    try {
      if (!username) {
        throw new Error('Please enter your username');
      }

      // Passkey 로그인 (토큰 자동 저장)
      await SecureAuthService.loginWithPasskey(username);
      
      setMessage('Login successful!');
      
      onLoginSuccess();     
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const onRegisterClick = async () => {
    setError('');
    setMessage('');
    setIsLoading(true);

    try {
      if (!username) {
        throw new Error('Please enter your username');
      }

      // Passkey 등록
      const result = await SecureAuthService.registerWithPasskey(username);
      
      if (result.success) {
        setMessage(result.message);
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const onGuestLogin = () => {
    // 게스트 로그인 (토큰 없이 진입)
    onLoginSuccess();
  };

  return (
    <div className="min-h-screen bg-gray-900 p-4">
      {/* 중앙 로그인 카드 */}
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-full max-w-md">
          <div className="bg-gray-800 rounded-lg shadow-xl p-8">
            {/* 타이틀 */}
            <h1 className="text-3xl font-bold text-white text-center mb-8">
              Trade Everything
            </h1>
            
            {/* Passkey 로그인 폼 */}
            <div className="space-y-6">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">
                  Username
                </label>
                <input
                  type="text"
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !isLoading) {
                      onLoginClick();
                    }
                  }}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your username"
                  disabled={isLoading}
                />
              </div>

              {message && (
                <div className="bg-green-900/50 border border-green-500 text-green-200 px-4 py-3 rounded-md">
                  {message}
                </div>
              )}

              {error && (
                <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-md">
                  {error}
                </div>
              )}

              <button
                onClick={onLoginClick}
                type="button"
                disabled={isLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800"
              >
                {isLoading ? 'Logging in...' : 'Login with Passkey'}
              </button>

              <button
                onClick={onRegisterClick}
                type="button"
                disabled={isLoading}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-800"
              >
                {isLoading ? 'Registering...' : 'Register with Passkey'}
              </button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-600"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-gray-800 text-gray-400">Or</span>
                </div>
              </div>

              <button
                onClick={onGuestLogin}
                type="button"
                disabled={isLoading}
                className="w-full bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-800"
              >
                Guest Login
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
