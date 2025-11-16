import React, { useEffect, useState } from 'react';
import { showToast } from '../Common/Toast';
import { SecureAuthService } from '../Auth/AuthService';
import { API_URL } from '../Common/Constants';

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

  // 모든 주문 취소
  const cancelAllOrders = async () => {
    try {
      showToast.success(`All orders have been canceled. (#orders = ${openOrders.length})`);
      // TODO: 실제 취소 API 호출
      await fetchOrders(); // 주문 목록 갱신
    } catch (error) {
      showToast.error('Failed to cancel orders');
    }
  };

  // 개별 주문 취소
  const cancelOrder = async (orderId: string) => {
    try {
      showToast.success(`Order ${orderId} has been canceled`);
      // TODO: 실제 취소 API 호출
      await fetchOrders(); // 주문 목록 갱신
    } catch (error) {
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
                onClick={() => cancelOrder(order.order_id)}
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
