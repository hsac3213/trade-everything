import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

interface BrokerContextType {
  broker: string;
  setBroker: (broker: string) => void;
  symbol: string;
  setSymbol: (symbol: string) => void;
}

const BrokerContext = createContext<BrokerContextType | undefined>(undefined);

export const BrokerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [broker, setBroker] = useState<string>('Binance');
  const [symbol, setSymbol] = useState<string>('btcusdt');

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
