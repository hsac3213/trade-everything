import React from 'react';
import { showToast } from './Toast';

/**
 * 토스트 사용 예제 컴포넌트
 * 실제 사용 시 이 파일은 삭제하고 showToast만 import해서 사용하세요.
 */
const ToastExample: React.FC = () => {
  
  // 예제 1: 기본 토스트
  const handleSuccess = () => {
    showToast.success('주문이 성공적으로 완료되었습니다!');
  };

  const handleError = () => {
    showToast.error('주문 실패: 잔액이 부족합니다');
  };

  const handleInfo = () => {
    showToast.info('새로운 알림이 있습니다');
  };

  const handleWarning = () => {
    showToast.warning('연결이 불안정합니다');
  };

  // 예제 2: 커스텀 시간 설정
  const handleCustomDuration = () => {
    showToast.success('5초 동안 표시됩니다', 5000);
  };

  // 예제 3: 로딩 토스트
  const handleLoading = () => {
    const loadingToast = showToast.loading('데이터를 불러오는 중...');
    
    // 3초 후 성공 토스트로 변경
    setTimeout(() => {
      showToast.dismiss(loadingToast);
      showToast.success('데이터 로드 완료!');
    }, 3000);
  };

  // 예제 4: Promise 토스트 (가장 유용!)
  const handlePromiseToast = async () => {
    const mockApiCall = new Promise((resolve, reject) => {
      setTimeout(() => {
        // 50% 확률로 성공/실패
        Math.random() > 0.5 ? resolve('데이터') : reject('에러');
      }, 2000);
    });

    showToast.promise(mockApiCall, {
      loading: '주문 처리 중...',
      success: '주문이 완료되었습니다!',
      error: '주문 실패: 다시 시도해주세요',
    });
  };

  // 예제 5: 실제 API 호출과 함께 사용
  const handleOrderSubmit = async () => {
    const submitOrder = async () => {
      const response = await fetch('http://localhost:8001/api/order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: 'BTCUSDT', amount: 0.01 }),
      });
      
      if (!response.ok) throw new Error('주문 실패');
      return response.json();
    };

    showToast.promise(submitOrder(), {
      loading: '주문 제출 중...',
      success: (data) => `주문 완료! ID: ${data.orderId}`,
      error: (err) => `주문 실패: ${err.message}`,
    });
  };

  return (
    <div className="p-8 space-y-4">
      <h2 className="text-2xl font-bold mb-6">토스트 알림 예제</h2>
      
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">기본 토스트</h3>
        <div className="flex gap-2">
          <button
            onClick={handleSuccess}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-white"
          >
            Success Toast
          </button>
          <button
            onClick={handleError}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-white"
          >
            Error Toast
          </button>
          <button
            onClick={handleInfo}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
          >
            Info Toast
          </button>
          <button
            onClick={handleWarning}
            className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded text-white"
          >
            Warning Toast
          </button>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-lg font-semibold">커스텀 & 고급 기능</h3>
        <div className="flex gap-2">
          <button
            onClick={handleCustomDuration}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded text-white"
          >
            Custom Duration (5s)
          </button>
          <button
            onClick={handleLoading}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded text-white"
          >
            Loading Toast
          </button>
          <button
            onClick={handlePromiseToast}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded text-white"
          >
            Promise Toast
          </button>
        </div>
      </div>

      <div className="mt-8 p-4 bg-gray-800 rounded">
        <h3 className="text-lg font-semibold mb-2">실제 사용법:</h3>
        <pre className="text-sm text-gray-300">
{`// 1. Toast import
import { showToast } from '@/Common/Toast';

// 2. 컴포넌트에서 사용
const MyComponent = () => {
  const handleClick = () => {
    showToast.success('성공!');
  };
  
  return <button onClick={handleClick}>클릭</button>;
};

// 3. API 호출과 함께 사용
const handleApiCall = async () => {
  try {
    const response = await fetch('/api/endpoint');
    if (response.ok) {
      showToast.success('데이터 로드 완료!');
    }
  } catch (error) {
    showToast.error('에러 발생!');
  }
};

// 4. Promise와 함께 사용 (권장)
showToast.promise(
  fetch('/api/endpoint').then(r => r.json()),
  {
    loading: '로딩 중...',
    success: '성공!',
    error: '실패!',
  }
);`}
        </pre>
      </div>
    </div>
  );
};

export default ToastExample;
