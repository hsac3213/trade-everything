import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries } from 'lightweight-charts';
import type { CandlestickData, IChartApi } from 'lightweight-charts';

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
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<any>(null);
  const [candleData, setCandleData] = useState<CandlestickData[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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
        console.log('Fetching candle data from:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.message === 'success' && data.candles && Array.isArray(data.candles)) {
          console.log(`✅ Loaded ${data.candles.length} candles`);
          setCandleData(data.candles);
        } else {
          throw new Error(data.error || 'Invalid response format');
        }
      } catch (err) {
        console.error('Failed to fetch candle data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchCandleData();
  }, [broker, symbol, interval, startTime]);

  useEffect(() => {
    if (!chartContainerRef.current || candleData.length === 0) return;

    const chartWidth = typeof width === 'string' && width.endsWith('px')
      ? parseInt(width)
      : chartContainerRef.current.clientWidth;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: backgroundColor },
        textColor: textColor,
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

    // lightweight-charts v5 - use CandlestickSeries
    const candlestickSeries = chart.addSeries(CandlestickSeries);
    
    // Apply candlestick options
    candlestickSeries.applyOptions({
      upColor: upColor,
      downColor: downColor,
      borderVisible: false,
      wickUpColor: upColor,
      wickDownColor: downColor,
    });

    candlestickSeries.setData(candleData);
    chart.timeScale().fitContent();

    chartRef.current = chart;
    seriesRef.current = candlestickSeries;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        const chartWidth = typeof width === 'string' && width.endsWith('px')
          ? parseInt(width)
          : chartContainerRef.current.clientWidth;
        
        chartRef.current.applyOptions({
          width: chartWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [candleData, height, width, backgroundColor, textColor, upColor, downColor]);

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
      ref={chartContainerRef} 
      style={{ 
        width: width, 
        height: `${height}px`,
      }} 
    />
  );
}

export default CandleChart;
