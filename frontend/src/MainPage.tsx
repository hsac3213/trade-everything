import React, { useState } from 'react';
import Trade from './Trade/Trade';
import Assets from './Assets';
import Script from './Script';
import License from './License';
import { ToastContainer } from './Common/Toast';
import { BrokerProvider } from './Context/BrokerContext';
import { WebSocketProvider } from './Context/WebSocketContext';

// --- 메뉴 헤더 컴포넌트 ---
interface MenuHeaderProps {
  activeMenu: string;
  onMenuChange: (menu: string) => void;
  menuItems: string[];
}

const MenuHeader: React.FC<MenuHeaderProps> = ({ activeMenu, onMenuChange, menuItems }) => {
  return (
    <div className="flex items-center gap-6">
      <h1 className="text-3xl font-bold text-gray-100">
        Trade Everything
      </h1>
      <div className="flex gap-1">
        {menuItems.map((menu) => (
          <button
            key={menu}
            onClick={() => onMenuChange(menu)}
            className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
              activeMenu === menu
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            {menu}
          </button>
        ))}
      </div>
    </div>
  );
};

// --- 메인 거래 컴포넌트 ---
const TradeMain: React.FC = () => {
  const menuItems = ['Trade', 'Assets', 'Script', 'License'];
  const [activeMenu, setActiveMenu] = useState<string>('Trade');

  // 메뉴별 컨텐츠 렌더링
  const renderContent = () => {
    switch (activeMenu) {
      case 'Trade':
        return (
          <>
            <MenuHeader activeMenu={activeMenu} onMenuChange={setActiveMenu} menuItems={menuItems} />
            <Trade />
          </>
        );
      
      case 'Assets':
        return (
          <>
            <MenuHeader activeMenu={activeMenu} onMenuChange={setActiveMenu} menuItems={menuItems} />
            <Assets />
          </>
        );
      
      case 'Script':
        return (
          <>
            <MenuHeader activeMenu={activeMenu} onMenuChange={setActiveMenu} menuItems={menuItems} />
            <Script />
          </>
        );
      
      case 'License':
        return (
          <>
            <MenuHeader activeMenu={activeMenu} onMenuChange={setActiveMenu} menuItems={menuItems} />
            <License />
          </>
        );
      
      default:
        return null;
    }
  };

  return (
    <BrokerProvider>
      <WebSocketProvider>
        <div className="min-h-screen bg-gray-900 text-white p-4 lg:p-8 font-sans">
          <div className="flex flex-col gap-3 flex-1">
            {/* 메인 레이아웃 - 메뉴별 컨텐츠 */}
            {renderContent()}
          </div>
          
          {/* 토스트 알림 컨테이너 */}
          <ToastContainer />
        </div>
      </WebSocketProvider>
    </BrokerProvider>
  );
}

export default TradeMain;
