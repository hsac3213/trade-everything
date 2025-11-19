import React, { createContext, useContext, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { WS_URL } from '../Common/Constants';
import { SecureAuthService } from '../Auth/AuthService';

interface WebSocketContextType {
  subscribeOrderbook: (broker: string, symbol: string, callback: (data: any) => void) => () => void;
  subscribeTradePrice: (broker: string, symbol: string, callback: (data: any) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const WebSocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // WebSocket 연결들을 저장 (key: "broker-symbol-type")
  const connectionsRef = useRef<Map<string, WebSocket>>(new Map());
  // 각 구독의 콜백 함수들 (여러 컴포넌트가 같은 데이터를 구독할 수 있음)
  const callbacksRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());

  const subscribeOrderbook = (broker: string, symbol: string, callback: (data: any) => void): (() => void) => {
    const key = `${broker}-${symbol}-orderbook`;
    
    // 콜백 등록
    if (!callbacksRef.current.has(key)) {
      callbacksRef.current.set(key, new Set());
    }
    callbacksRef.current.get(key)!.add(callback);

    // WebSocket이 이미 존재하면 새로 생성하지 않음
    if (!connectionsRef.current.has(key)) {
      // WebSocket 연결 생성
      const ws = new WebSocket(`${WS_URL}/ws/orderbook/${broker}/${symbol}`);
      
      ws.onopen = () => {
        console.log(`✅ WebSocket connected: ${key}`);
        // 연결 후 JWT 토큰 전송
        const token = SecureAuthService.getAccessToken();
        if (token) {
          ws.send(JSON.stringify({ token }));
          console.log(`🔑 Token sent for ${key}`);
        } else {
          console.error(`❌ No token available for ${key}`);
          ws.close(1008, 'No authentication token');
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // 인증 응답 처리
          if (data.type === 'authenticated') {
            console.log(`🔐 Orderbook authenticated for ${key}`);
            return;
          }
          
          // 에러 응답 처리
          if (data.type === 'error') {
            console.error(`❌ Orderbook authentication error for ${key}:`, data.message);
            ws.close(1008, 'Authentication failed');
            return;
          }
          
          // ping 메시지 무시
          if (data.type === 'ping') {
            return;
          }
          
          // 등록된 모든 콜백 호출
          const callbacks = callbacksRef.current.get(key);
          if (callbacks) {
            callbacks.forEach(cb => {
              try {
                cb(data);
              } catch (error) {
                console.error('Callback error:', error);
              }
            });
          }
        } catch (error) {
          console.error('Error parsing WebSocket data:', error);
        }
      };

      ws.onerror = (error) => {
        console.error(`❌ WebSocket error for ${key}:`, error);
      };

      ws.onclose = () => {
        console.log(`🔌 WebSocket closed for ${key}`);
        connectionsRef.current.delete(key);
      };

      connectionsRef.current.set(key, ws);
    }

    // unsubscribe 함수 반환
    return () => {
      const callbacks = callbacksRef.current.get(key);
      if (callbacks) {
        callbacks.delete(callback);
        
        // 모든 콜백이 제거되면 WebSocket 닫기
        if (callbacks.size === 0) {
          const ws = connectionsRef.current.get(key);
          if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
            ws.close();
          }
          connectionsRef.current.delete(key);
          callbacksRef.current.delete(key);
        }
      }
    };
  };

  const subscribeTradePrice = (broker: string, symbol: string, callback: (data: any) => void): (() => void) => {
    const key = `${broker}-${symbol}-trade`;
    
    if (!callbacksRef.current.has(key)) {
      callbacksRef.current.set(key, new Set());
    }
    callbacksRef.current.get(key)!.add(callback);

    if (!connectionsRef.current.has(key)) {
      const ws = new WebSocket(`${WS_URL}/ws/trade/${broker}/${symbol}`);
      
      ws.onopen = () => {
        console.log(`✅ WebSocket connected: ${key}`);
        // 연결 후 JWT 토큰 전송
        const token = SecureAuthService.getAccessToken();
        if (token) {
          ws.send(JSON.stringify({ token }));
          console.log(`🔑 Token sent for ${key}`);
        } else {
          console.error(`❌ No token available for ${key}`);
          ws.close(1008, 'No authentication token');
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // 인증 응답 처리
          if (data.type === 'authenticated') {
            console.log(`🔐 Trade authenticated for ${key}`);
            return;
          }
          
          // 에러 응답 처리
          if (data.type === 'error') {
            console.error(`❌ Trade authentication error for ${key}:`, data.message);
            ws.close(1008, 'Authentication failed');
            return;
          }
          
          if (data.type === 'ping') {
            return;
          }
          
          const callbacks = callbacksRef.current.get(key);
          if (callbacks) {
            callbacks.forEach(cb => {
              try {
                cb(data);
              } catch (error) {
                console.error('Callback error:', error);
              }
            });
          }
        } catch (error) {
          console.error('Error parsing WebSocket data:', error);
        }
      };

      ws.onerror = (error) => {
        console.error(`❌ WebSocket error for ${key}:`, error);
      };

      ws.onclose = () => {
        console.log(`🔌 WebSocket closed for ${key}`);
        connectionsRef.current.delete(key);
      };

      connectionsRef.current.set(key, ws);
    }

    return () => {
      const callbacks = callbacksRef.current.get(key);
      if (callbacks) {
        callbacks.delete(callback);
        
        if (callbacks.size === 0) {
          const ws = connectionsRef.current.get(key);
          if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
            ws.close();
          }
          connectionsRef.current.delete(key);
          callbacksRef.current.delete(key);
        }
      }
    };
  };

  // 컴포넌트 unmount 시 모든 WebSocket 정리
  useEffect(() => {
    return () => {
      connectionsRef.current.forEach(ws => {
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close();
        }
      });
      connectionsRef.current.clear();
      callbacksRef.current.clear();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ 
      subscribeOrderbook, 
      subscribeTradePrice
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};
