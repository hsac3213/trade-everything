import { useEffect, useState } from 'react';
import { WS_URL } from '../Common/Constants';
import { SecureAuthService } from '../Auth/AuthService';

interface TradeData {
  price: string;
  volume?: string;
  quantity?: string;
  timestamp?: number;
  side?: string;
  isBuyerMaker?: boolean;
}

// 전역 공유 상태
const sharedState = {
  ws: null as WebSocket | null,
  data: null as TradeData | null,
  listeners: new Set<(data: TradeData) => void>(),
  subscription: null as { broker: string; symbol: string } | null,
};

/**
 * 여러 컴포넌트에서 하나의 WebSocket 연결을 공유하는 Hook
 * 
 * @param broker - 브로커 이름 (예: 'Binance')
 * @param symbol - 심볼 (예: 'btcusdt')
 * @returns 실시간 체결 데이터
 * 
 * @example
 * const tradeData = useSharedTradeWebSocket('Binance', 'btcusdt');
 * console.log(tradeData?.price); // 현재 체결가
 */
export const useSharedTradeWebSocket = (broker: string, symbol: string): TradeData | null => {
  const [tradeData, setTradeData] = useState<TradeData | null>(sharedState.data);

  useEffect(() => {
    // 리스너 등록
    const listener = (data: TradeData) => setTradeData(data);
    sharedState.listeners.add(listener);

    // 같은 broker/symbol이 아니면 재연결
    const needsReconnect = 
      !sharedState.subscription ||
      sharedState.subscription.broker !== broker || 
      sharedState.subscription.symbol !== symbol;

    if (needsReconnect) {
      // 기존 연결 종료
      if (sharedState.ws) {
        console.log('🔄 Switching WebSocket connection to:', broker, symbol);
        sharedState.ws.close();
        sharedState.ws = null;
      }

      // 새 연결 생성
      sharedState.subscription = { broker, symbol };
      const ws = new WebSocket(`${WS_URL}/ws/trade/${broker}/${symbol}`);
      
      ws.onopen = () => {
        console.log('✅ Shared WebSocket connected:', broker, symbol);
        // 연결 후 JWT 토큰 전송
        const token = SecureAuthService.getAccessToken();
        if (token) {
          ws.send(JSON.stringify({ token }));
          console.log('🔑 Token sent for shared trade WebSocket');
        } else {
          console.error('❌ No token available for shared trade WebSocket');
          ws.close(1008, 'No authentication token');
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // 인증 응답 처리
          if (data.type === 'authenticated') {
            console.log('🔐 Shared Trade authenticated');
            return;
          }
          
          // 에러 응답 처리
          if (data.type === 'error') {
            console.error('❌ Shared Trade authentication error:', data.message);
            ws.close(1008, 'Authentication failed');
            return;
          }
          
          sharedState.data = data;
          // 모든 리스너에게 데이터 전달
          sharedState.listeners.forEach(l => l(data));
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('🔌 Shared WebSocket disconnected');
      };

      sharedState.ws = ws;
    } else if (sharedState.data) {
      // 이미 연결되어 있고 데이터가 있으면 즉시 전달
      setTradeData(sharedState.data);
    }

    // 클린업: 리스너 제거
    return () => {
      sharedState.listeners.delete(listener);
      
      // 마지막 리스너가 사라지면 연결 종료
      if (sharedState.listeners.size === 0) {
        console.log('🧹 No more listeners, closing shared WebSocket');
        if (sharedState.ws) {
          sharedState.ws.close();
          sharedState.ws = null;
        }
        sharedState.subscription = null;
        sharedState.data = null;
      }
    };
  }, [broker, symbol]);

  return tradeData;
};
