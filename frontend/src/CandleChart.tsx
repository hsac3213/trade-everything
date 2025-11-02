import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
import type { CandlestickData, IChartApi, HistogramData, Time } from 'lightweight-charts';

// 볼륨 정보를 포함한 캔들 데이터 타입
interface CandleWithVolume extends CandlestickData {
  volume?: number;
}

interface CandleChartProps {
  broker?: string;
  symbol?: string;
  interval?: string;
  startTime?: string;
  height?: number;
  width?: string;
  backgroundColor?: string;
  textColor?: string;
  upColor?: string;
  downColor?: string;
}

function CandleChart({
  broker = 'Binance',
  symbol = 'BTCUSDT',
  interval = '1h',
  startTime,
  height = 600,
  width = '100%',
  backgroundColor = '#1e1e1e',
  textColor = '#d1d4dc',
  upColor = '#26a69a',
  downColor = '#ef5350',
}: CandleChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const legendRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);
  const [candleData, setCandleData] = useState<CandleWithVolume[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // broker나 symbol이 변경되면 즉시 차트 초기화
  useEffect(() => {
    console.log(`🔄 [CandleChart] Broker or Symbol changed: ${broker}/${symbol} - Clearing chart data`);
    
    // 1. 데이터 초기화
    setCandleData([]);
    setIsLoading(true);
    setError(null);
    
    // 2. 기존 차트 제거
    if (chartRef.current) {
      console.log('🗑️ [CandleChart] Removing existing chart instance');
      chartRef.current.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    }
    
    console.log('✅ [CandleChart] Chart cleared, ready to load new data');
  }, [broker, symbol]);

  useEffect(() => {
    const fetchCandleData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const defaultStartTime = startTime || (() => {
          const date = new Date();
          date.setDate(date.getDate() - 30);
          return date.toISOString().slice(0, 19).replace('T', ' ');
        })();
        
        const url = `http://localhost:8001/candle/${broker}?symbol=${symbol}&interval=${interval}&start_time=${encodeURIComponent(defaultStartTime)}`;
        console.log(`📡 [CandleChart] Fetching candle data from: ${url}`);
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.message === 'success' && data.candles && Array.isArray(data.candles)) {
          console.log(`✅ [CandleChart] Loaded ${data.candles.length} candles for ${broker}/${symbol}`);
          setCandleData(data.candles);
        } else {
          throw new Error(data.error || 'Invalid response format');
        }
      } catch (err) {
        console.error(`❌ [CandleChart] Failed to fetch candle data:`, err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchCandleData();
  }, [broker, symbol, interval, startTime]);

  useEffect(() => {
    if (!chartContainerRef.current || candleData.length === 0) return;
    
    console.log(`📈 [CandleChart] Creating chart with ${candleData.length} candles for ${broker}/${symbol}`);

    const chartWidth = typeof width === 'string' && width.endsWith('px')
      ? parseInt(width)
      : chartContainerRef.current.clientWidth;

    // === 하나의 차트 생성 (캔들과 볼륨을 별도 pane에 배치) ===
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: backgroundColor },
        textColor: textColor,
        panes: {
          separatorColor: '#2b2b43',
          separatorHoverColor: 'rgba(100, 100, 100, 0.3)',
          enableResize: true, // 사용자가 pane 크기 조절 가능
        },
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
        rightOffset: 12,
        barSpacing: 6,
        rightBarStaysOnScroll: false,
        fixLeftEdge: false,
        fixRightEdge: false,
      },
      crosshair: {
        mode: 1, // Normal crosshair mode
        vertLine: {
          width: 1,
          color: '#758696',
          style: 3, // Dashed
        },
        horzLine: {
          width: 1,
          color: '#758696',
          style: 3, // Dashed
        },
      },
      localization: {
        locale: 'ko-KR',
        timeFormatter: (time: any) => {
          const date = new Date(time * 1000);
          return date.toLocaleDateString('ko-KR', { 
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          });
        },
      },
    });

    // === 1. 캔들스틱 시리즈 추가 (pane 0 - 기본 pane) ===
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: upColor,
      downColor: downColor,
      borderVisible: false,
      wickUpColor: upColor,
      wickDownColor: downColor,
    });

    candlestickSeries.setData(candleData);

    // === 2. 볼륨 히스토그램 시리즈 추가 (pane 1 - 새로운 pane) ===
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: {
        type: 'volume',
      },
    }, 1); // pane index 1 지정

    // 볼륨 데이터 변환 및 설정
    const volumeData = candleData.map(candle => ({
      time: candle.time,
      value: candle.volume || 0,
      color: (candle.close >= candle.open) ? upColor : downColor,
    }));
    
    volumeSeries.setData(volumeData);

    // 볼륨 pane을 아래로 이동하고 높이 설정
    const volumePane = chart.panes()[1];
    if (volumePane) {
      volumePane.setHeight(Math.floor(height * 0.3)); // 전체의 30%
    }

    // 초기 범위 설정
    chart.timeScale().fitContent();

    // === 3. Legend (OHLC 정보 표시) 설정 ===
    if (legendRef.current) {
      const updateLegend = (param: any) => {
        if (!legendRef.current) return;
        
        if (param.time && param.seriesData.get(candlestickSeries)) {
          const data = param.seriesData.get(candlestickSeries) as CandlestickData;
          const open = data.open.toFixed(2);
          const high = data.high.toFixed(2);
          const low = data.low.toFixed(2);
          const close = data.close.toFixed(2);
          const candleColor = data.close >= data.open ? upColor : downColor;
          
          legendRef.current.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
              <strong style="color: ${textColor};">${symbol}</strong>
              <span style="color: #888;">O</span> <strong style="color: ${candleColor};">${open}</strong>
              <span style="color: #888;">H</span> <strong style="color: ${candleColor};">${high}</strong>
              <span style="color: #888;">L</span> <strong style="color: ${candleColor};">${low}</strong>
              <span style="color: #888;">C</span> <strong style="color: ${candleColor};">${close}</strong>
            </div>
          `;
        } else {
          // 마우스가 차트 밖으로 나가면 기본 정보만 표시
          legendRef.current.innerHTML = `
            <div style="color: ${textColor};">
              <strong>${symbol}</strong>
            </div>
          `;
        }
      };
      
      chart.subscribeCrosshairMove(updateLegend);
      
      // 초기 legend 표시
      legendRef.current.innerHTML = `
        <div style="color: ${textColor};">
          <strong>${symbol}</strong>
        </div>
      `;
    }

    chartRef.current = chart;
    candleSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        const chartWidth = typeof width === 'string' && width.endsWith('px')
          ? parseInt(width)
          : chartContainerRef.current.clientWidth;
        
        chartRef.current.applyOptions({
          width: chartWidth,
          height: height,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [candleData, height, width, backgroundColor, textColor, upColor, downColor, symbol]);

  if (isLoading) {
    return (
      <div 
        style={{ 
          width: width, 
          height: `${height}px`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: backgroundColor,
          color: textColor,
        }}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4">Loading candle data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div 
        style={{ 
          width: width, 
          height: `${height}px`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: backgroundColor,
          color: '#ef5350',
        }}
      >
        <div className="text-center">
          <p className="text-lg font-semibold">Error loading data</p>
          <p className="mt-2">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      style={{ 
        width: width, 
        height: `${height}px`,
        position: 'relative',
      }} 
    >
      {/* Legend (OHLC 정보) */}
      <div 
        ref={legendRef}
        style={{
          position: 'absolute',
          left: '12px',
          top: '12px',
          zIndex: 10,
          fontSize: '14px',
          fontFamily: 'sans-serif',
          lineHeight: '18px',
          fontWeight: 300,
          pointerEvents: 'none', // 마우스 이벤트 통과
          backgroundColor: 'rgba(0, 0, 0, 0.5)', // 배경 추가 (가독성)
          padding: '8px 12px',
          borderRadius: '4px',
        }}
      >
        <div style={{ color: textColor }}>
          <strong>{symbol}</strong>
        </div>
      </div>
      
      {/* 단일 차트 (캔들 + 볼륨) */}
      <div 
        ref={chartContainerRef} 
        style={{ 
          width: '100%', 
          height: '100%',
        }} 
      />
    </div>
  );
}

export default CandleChart;
