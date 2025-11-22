import React, { useEffect, useState, useRef } from 'react';
import { showToast } from '../Common/Toast';
import { SecureAuthService } from '../Auth/AuthService';
import { API_URL, WS_URL } from '../Common/Constants';

// --- 타입 정의 ---
interface OpenOrder {
  order_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  price: string;
  amount: string;
}

interface OpenOrderProps {
  broker: string;
  onRefreshRequest?: (refreshFn: () => void) => void;
}

// --- Open Orders 컴포넌트 ---
const OpenOrder: React.FC<OpenOrderProps> = ({ broker, onRefreshRequest }) => {
  const [openOrders, setOpenOrders] = useState<OpenOrder[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // 주문 목록 가져오기
  const fetchOrders = async () => {
    console.log("fetchOrders");
    setIsLoading(true);
    try {
      const token = SecureAuthService.getAccessToken();
      const response = await fetch(`${API_URL}/orders/${broker}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      console.log(response);
      
      const data = await response.json();
      
      if (data.message === 'success') {
        setOpenOrders(data.orders || []);
      } else {
        showToast.error(`Failed to fetch orders: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error fetching orders:', error);
      showToast.error('Failed to fetch orders');
    } finally {
      setIsLoading(false);
    }
  };

  // 컴포넌트 마운트 시 주문 목록 가져오기
  useEffect(() => {
    fetchOrders();
    
    // 부모 컴포넌트에 refresh 함수 전달
    if (onRefreshRequest) {
      onRefreshRequest(fetchOrders);
    }
  }, [broker]);

  // WebSocket 구독 - 주문 업데이트 실시간 수신
  useEffect(() => {
    // 기존 연결 종료
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // 새 WebSocket 연결
    const ws = new WebSocket(`${WS_URL}/ws/order_update/${broker}`);
    
    ws.onopen = () => {
      console.log(`✅ Order update WebSocket connected: ${broker}`);
      // 인증 토큰 전송
      const token = SecureAuthService.getAccessToken();
      if (token) {
        ws.send(JSON.stringify({ token }));
        console.log(`Token sent for order update`);
      } else {
        console.error(`No token available for order update`);
        ws.close(1008, 'No authentication token');
      }
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        // 인증 응답 처리
        if (message.type === 'authenticated') {
          console.log(`Order update authenticated`);
          return;
        }
        
        // 에러 응답 처리
        if (message.type === 'error') {
          console.error(`Order update error:`, message.message);
          return;
        }
        
        // 주문 업데이트 데이터 처리
        if (message.type === 'userdata' && message.data) {
          const orderData = message.data;
          console.log('Order update received:', orderData);
          
          // 주문 체결
          if (orderData.order_status === 'TRADE') {
            setOpenOrders(prev => 
              prev.filter(order => order.order_id !== orderData.order_id)
            );
            showToast.success(`Order filled: ${orderData.symbol} ${orderData.side} @ ${orderData.price}`);
          }
          // 주문 취소
          else if (orderData.order_status === 'CANCELED') {
            setOpenOrders(prev => 
              prev.filter(order => order.order_id !== orderData.order_id)
            );
            showToast.info(`Order canceled: ${orderData.symbol} ${orderData.side}`);
          }
          // 새 주문
          else if (orderData.order_status === 'NEW') {
            // 이미 목록에 없으면 추가
            setOpenOrders(prev => {
              const exists = prev.some(order => order.order_id === orderData.order_id);
              if (!exists) {
                return [...prev, {
                  order_id: orderData.order_id,
                  symbol: orderData.symbol,
                  side: orderData.side,
                  price: orderData.price,
                  amount: orderData.quantity
                }];
              }
              return prev;
            });
          }
        }
      } catch (error) {
        console.error('Error parsing order update:', error);
      }
    };

    ws.onerror = (error) => {
      console.error(`❌ Order update WebSocket error:`, error);
    };

    ws.onclose = () => {
      console.log(`🔌 Order update WebSocket closed`);
    };

    wsRef.current = ws;

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [broker]);

  // 모든 주문 취소
  const cancelAllOrders = async () => {
    try {
      const token = SecureAuthService.getAccessToken();
      
      const resp = await fetch(`${API_URL}/cancel_all_orders/${broker}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const resp_json = await resp.json();

      // 결과 표시
      if (resp_json.message === 'success') {
        showToast.success('All orders canceled successfully');
      } else {
        showToast.error(`Failed to cancel orders: ${resp_json.error || 'Unknown error'}`);
      }

      // 주문 목록 갱신
      await fetchOrders();
    } catch (error) {
      console.error('Error in cancelAllOrders:', error);
      showToast.error('Failed to cancel orders');
    }
  };

  // 개별 주문 취소
  const cancelOrder = async (orderId: string, symbol: string) => {
    try {
      const token = SecureAuthService.getAccessToken();
      const response = await fetch(`${API_URL}/cancel_order/${broker}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          symbol: symbol,
          order_id: orderId
        })
      });

      const data = await response.json();
      
      if (data.message === 'success') {
        showToast.success(`Order ${orderId} canceled`);
        await fetchOrders(); // 주문 목록 갱신
      } else {
        showToast.error(`Failed to cancel order: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error canceling order:', error);
      showToast.error('Failed to cancel order');
    }
  };

  return (
    <div className="flex-1 bg-gray-900 rounded-lg p-3 flex flex-col">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-base font-semibold text-gray-200">
          Open Orders {isLoading && <span className="text-xs text-gray-400">(Loading...)</span>}
        </h3>
        
        {/* Cancel All 버튼 */}
        <button 
          className="px-4 py-1.5 bg-red-600 hover:bg-red-700 rounded text-sm font-medium transition-colors disabled:bg-gray-600 disabled:cursor-not-allowed"
          onClick={cancelAllOrders}
        >
          Cancel All
        </button>
      </div>
      
      {/* 주문 목록 헤더 */}
      <div className="grid grid-cols-5 gap-4 mb-1 text-xs text-gray-400 font-medium">
        <span>Symbol</span>
        <span>Side</span>
        <span>Price</span>
        <span>Amount</span>
        <span className="text-center"></span>
      </div>
      
      {/* 주문 목록 */}
      <div className="overflow-y-auto space-y-1.5 max-h-[400px]">
        {openOrders.length > 0 ? (
          openOrders.map((order) => (
            <div
              key={order.order_id}
              className="grid grid-cols-5 gap-4 p-2 bg-gray-800 rounded-md text-sm items-center"
            >
              <span className="font-mono text-xs">{order.symbol}</span>
              <span className={`font-semibold ${order.side === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                {order.side.toUpperCase()}
              </span>
              <span className="font-mono text-xs">{order.price}</span>
              <span className="font-mono text-xs">{order.amount}</span>
              <button 
                className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs transition-colors"
                onClick={() => cancelOrder(order.order_id, order.symbol)}
              >
                Cancel
              </button>
            </div>
          ))
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            {isLoading ? 'Loading...' : 'No open orders'}
          </div>
        )}
      </div>
    </div>
  );
};

export default OpenOrder;
