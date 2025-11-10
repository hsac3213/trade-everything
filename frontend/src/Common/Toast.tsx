import toast, { Toaster } from 'react-hot-toast';
import type { Toast as ToastType } from 'react-hot-toast';
import { useEffect, useState } from 'react';

/**
 * 프로그레스 바가 있는 커스텀 토스트 컴포넌트
 */
interface CustomToastProps {
  t: ToastType;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration: number;
}

const CustomToast: React.FC<CustomToastProps> = ({ t, message, type, duration }) => {
  const [progress, setProgress] = useState(100);
  
  useEffect(() => {
    const startTime = Date.now();
    
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);
      
      if (remaining === 0) {
        clearInterval(interval);
      }
    }, 10); // 10ms마다 업데이트
    
    return () => clearInterval(interval);
  }, [duration]);

  const getIcon = () => {
    switch (type) {
      case 'success': return '✓';
      case 'error': return '✕';
      case 'info': return 'ℹ';
      case 'warning': return '⚠';
      default: return '';
    }
  };

  const getColor = () => {
    switch (type) {
      case 'success': return '#10b981';
      case 'error': return '#ef4444';
      case 'info': return '#3b82f6';
      case 'warning': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  return (
    <div
      className={`${
        t.visible ? 'animate-enter' : 'animate-leave'
      } max-w-md w-full bg-gray-800 shadow-lg rounded-lg pointer-events-auto flex flex-col overflow-hidden`}
      style={{
        animation: t.visible
          ? 'toast-enter 0.2s ease-out'
          : 'toast-leave 0.15s ease-in forwards',
      }}
    >
      {/* 토스트 내용 */}
      <div className="flex items-center p-4">
        {/* 아이콘 */}
        <div
          className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white font-bold"
          style={{ backgroundColor: getColor() }}
        >
          {getIcon()}
        </div>
        
        {/* 메시지 */}
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium text-white">{message}</p>
        </div>
        
        {/* 닫기 버튼 */}
        <button
          onClick={() => toast.dismiss(t.id)}
          className="ml-4 flex-shrink-0 text-gray-400 hover:text-gray-200 transition-colors"
        >
          <span className="text-xl">×</span>
        </button>
      </div>
      
      {/* 프로그레스 바 */}
      <div className="w-full h-1 bg-gray-700">
        <div
          className="h-full"
          style={{
            width: `${progress}%`,
            backgroundColor: getColor(),
            transition: 'none',
          }}
        />
      </div>
    </div>
  );
};

/**
 * 토스트 알림 유틸리티
 * 
 * @example
 * import { showToast } from '@/Common/Toast';
 * 
 * showToast.success('주문이 완료되었습니다!');
 * showToast.error('주문 실패: 잔액이 부족합니다');
 * showToast.info('알림: 새로운 메시지가 있습니다');
 * showToast.warning('경고: 연결이 불안정합니다');
 */

export const showToast = {
  success: (message: string, duration?: number) => {
    const toastDuration = duration || 3000;
    toast.custom(
      (t) => <CustomToast t={t} message={message} type="success" duration={toastDuration} />,
      { duration: toastDuration }
    );
  },

  error: (message: string, duration?: number) => {
    const toastDuration = duration || 4000;
    toast.custom(
      (t) => <CustomToast t={t} message={message} type="error" duration={toastDuration} />,
      { duration: toastDuration }
    );
  },

  info: (message: string, duration?: number) => {
    const toastDuration = duration || 3000;
    toast.custom(
      (t) => <CustomToast t={t} message={message} type="info" duration={toastDuration} />,
      { duration: toastDuration }
    );
  },

  warning: (message: string, duration?: number) => {
    const toastDuration = duration || 3500;
    toast.custom(
      (t) => <CustomToast t={t} message={message} type="warning" duration={toastDuration} />,
      { duration: toastDuration }
    );
  },

  loading: (message: string) => {
    return toast.loading(message, {
      style: {
        background: '#6b7280',
        color: '#fff',
        fontWeight: '500',
      },
    });
  },

  dismiss: (toastId?: string) => {
    toast.dismiss(toastId);
  },

  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    },
    duration?: { success?: number; error?: number }
  ) => {
    const loadingToastId = toast.loading(messages.loading, {
      style: {
        background: '#6b7280',
        color: '#fff',
        fontWeight: '500',
      },
    });

    promise
      .then((data) => {
        toast.dismiss(loadingToastId);
        const successMessage =
          typeof messages.success === 'function'
            ? messages.success(data)
            : messages.success;
        showToast.success(successMessage, duration?.success);
      })
      .catch((error) => {
        toast.dismiss(loadingToastId);
        const errorMessage =
          typeof messages.error === 'function'
            ? messages.error(error)
            : messages.error;
        showToast.error(errorMessage, duration?.error);
      });

    return promise;
  },
};

/**
 * 토스트 컨테이너 컴포넌트
 * App.tsx 또는 MainPage.tsx의 최상위에 추가
 */
export const ToastContainer = () => {
  return (
    <Toaster
      position="bottom-right"
      reverseOrder={false}
      gutter={8}
      toastOptions={{
        duration: 3000,
        style: {
          background: '#363636',
          color: '#fff',
          padding: '12px 16px',
          borderRadius: '8px',
          fontSize: '14px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        },
      }}
    />
  );
};
