import React, { useState, useEffect } from 'react';
import Login from './Login';
import TradeMain from './MainPage';

// --- 메인 앱 컴포넌트 (라우팅 역할) ---
const App: React.FC = () => {
  // localStorage에서 로그인 상태 확인
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    const savedAuth = localStorage.getItem('isAuthenticated');
    return savedAuth === 'true';
  });

  // 로그인 상태가 변경될 때마다 localStorage에 저장
  useEffect(() => {
    localStorage.setItem('isAuthenticated', String(isAuthenticated));
  }, [isAuthenticated]);

  // 로그인 성공 시 호출될 함수
  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  // 로그아웃 함수 (필요시 TradeMain에 prop으로 전달 가능)
  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('isAuthenticated');
  };

  return (
    <>
      {isAuthenticated ? (
        <TradeMain onLogout={handleLogout} />
      ) : (
        <Login onLoginSuccess={handleLoginSuccess} />
      )}
    </>
  );
}

export default App;
