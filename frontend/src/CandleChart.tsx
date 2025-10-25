import { useEffect, useRef } from 'react';
import { createChart, ColorType, CandlestickSeries } from 'lightweight-charts';
import type { CandlestickData } from 'lightweight-charts';

// Props 타입 정의
interface CandleChartProps {
  data?: CandlestickData[]; // 외부에서 데이터를 받을 수 있음 (선택적)
  height?: number; // 차트 높이 (기본값: 600)
  width?: string; // 차트 너비 (기본값: '100%')
  backgroundColor?: string; // 배경색 (기본값: '#1e1e1e')
  textColor?: string; // 텍스트 색상 (기본값: '#d1d4dc')
  upColor?: string; // 상승 캔들 색상 (기본값: '#26a69a')
  downColor?: string; // 하락 캔들 색상 (기본값: '#ef5350')
}

function CandleChart({
  data,
  height = 600,
  width = '100%',
  backgroundColor = '#1e1e1e',
  textColor = '#d1d4dc',
  upColor = '#26a69a',
  downColor = '#ef5350',
}: CandleChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // width가 픽셀 단위 문자열인 경우 숫자로 변환
    const chartWidth = typeof width === 'string' && width.endsWith('px')
      ? parseInt(width)
      : chartContainerRef.current.clientWidth;

    // 차트 생성
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: backgroundColor },
        textColor: textColor,
        attributionLogo: true,
      },
      width: chartWidth,
      height: height,
      grid: {
        vertLines: { color: '#2b2b43' },
        horzLines: { color: '#2b2b43' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // 캔들스틱 시리즈 추가
    const candlestickSeries = chart.addSeries(CandlestickSeries);
    
    // 시리즈 스타일 옵션 설정
    candlestickSeries.applyOptions({
      upColor: upColor,
      downColor: downColor,
      borderVisible: false,
      wickUpColor: upColor,
      wickDownColor: downColor,
    });

    // 임의의 캔들 데이터 생성 함수
    const generateCandleData = (): CandlestickData[] => {
      const generatedData: CandlestickData[] = [];
      const basePrice = 50000;
      let currentPrice = basePrice;
      const startTime = Math.floor(Date.now() / 1000) - 86400 * 30; // 30일 전

      for (let i = 0; i < 100; i++) {
        const timestamp = startTime + i * 3600; // 1시간 간격
        
        // 랜덤한 가격 변동
        const change = (Math.random() - 0.5) * 2000;
        currentPrice += change;
        
        const open = currentPrice;
        const high = open + Math.random() * 1000;
        const low = open - Math.random() * 1000;
        const close = low + Math.random() * (high - low);

        generatedData.push({
          time: timestamp as any,
          open: parseFloat(open.toFixed(2)),
          high: parseFloat(high.toFixed(2)),
          low: parseFloat(low.toFixed(2)),
          close: parseFloat(close.toFixed(2)),
        });

        currentPrice = close;
      }

      return generatedData;
    };

    // 데이터 설정 (props로 받은 데이터가 있으면 사용, 없으면 임의 생성)
    const candleData = data || generateCandleData();
    candlestickSeries.setData(candleData);

    // 차트를 데이터에 맞게 자동 조정
    chart.timeScale().fitContent();

    // 반응형 처리
    const handleResize = () => {
      if (chartContainerRef.current) {
        const chartWidth = typeof width === 'string' && width.endsWith('px')
          ? parseInt(width)
          : chartContainerRef.current.clientWidth;
        
        chart.applyOptions({
          width: chartWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // 클린업
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, height, width, backgroundColor, textColor, upColor, downColor]);

  return (
    <div 
      ref={chartContainerRef} 
      style={{ 
        width: width, 
        height: `${height}px`,
      }} 
    />
  );
}

export default CandleChart;