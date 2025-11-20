import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

interface BrokerContextType {
  broker: string;
  setBroker: (broker: string) => void;
  symbol: string;
  setSymbol: (symbol: string) => void;
}

const BrokerContext = createContext<BrokerContextType | undefined>(undefined);

// 거래소별 기본 심볼
const DEFAULT_SYMBOLS: Record<string, string> = {
  'Binance': 'btcusdt',
  'KIS': 'nvda',
};

export const BrokerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // 메모리에만 저장 (localStorage 사용하지 않음)
  const [broker, setBrokerState] = useState<string>('Binance');
  const [brokerSymbols, setBrokerSymbols] = useState<Record<string, string>>({ ...DEFAULT_SYMBOLS });

  // 현재 거래소의 심볼
  const symbol = brokerSymbols[broker] || DEFAULT_SYMBOLS[broker] || 'btcusdt';

  // 거래소 변경
  const setBroker = (newBroker: string) => {
    console.log(`[BrokerContext] Changing broker from ${broker} to ${newBroker}`);
    setBrokerState(newBroker);
  };

  // 심볼 변경 (현재 거래소의 심볼만 업데이트)
  const setSymbol = (newSymbol: string) => {
    console.log(`[BrokerContext] Changing symbol for ${broker} from ${symbol} to ${newSymbol}`);
    setBrokerSymbols(prev => ({
      ...prev,
      [broker]: newSymbol
    }));
  };

  // 디버깅용 로그
  useEffect(() => {
    console.log(`[BrokerContext] Current state - broker: ${broker}, symbol: ${symbol}`);
  }, [broker, symbol]);

  return (
    <BrokerContext.Provider value={{ broker, setBroker, symbol, setSymbol }}>
      {children}
    </BrokerContext.Provider>
  );
};

export const useBroker = () => {
  const context = useContext(BrokerContext);
  if (!context) {
    throw new Error('useBroker must be used within BrokerProvider');
  }
  return context;
};
