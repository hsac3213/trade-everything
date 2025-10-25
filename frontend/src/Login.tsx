import React, { useState } from 'react';
import { handleLogin, handleRegister } from './Passkey';

interface LoginProps {
  onLoginSuccess: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const onLoginClick = async () => {
    setError('');
    setMessage('');
    setIsLoading(true);

    onLoginSuccess();

    try {
      if (!email) {
        throw new Error('Please enter your email');
      }

      const result = await handleLogin(email);
      
      if (result.success) {
        setMessage(result.message);
        // 로그인 성공 시
        onLoginSuccess();
      } else {
        setError(result.message);
      }
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
      if (!email) {
        throw new Error('Please enter your email');
      }

      const result = await handleRegister(email);
      
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

  return (
    <div className="min-h-screen bg-gray-900 p-4">
      {/* 중앙 로그인 카드 */}
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-full max-w-md">
          <div className="bg-gray-800 rounded-lg shadow-xl p-8">
            {/* Passkey 로그인 폼 */}
            <div className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                  Email
                </label>
                <input
                  type="text"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your email."
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
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;