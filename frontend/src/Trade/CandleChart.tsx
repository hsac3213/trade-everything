import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
import type { CandlestickData, IChartApi, Time } from 'lightweight-charts';
import { API_URL } from '../Common/Constants';
import { useSharedTradeWebSocket } from '../Common/useSharedTradeWebSocket';
import { SecureAuthService } from '../Auth/AuthService';

const CANDLE_API_URL = `${API_URL}/candle`;

// 볼륨 정보를 포함한 캔들 데이터 타입
interface CandleWithVolume extends CandlestickData {
  volume?: number;
}

// Datafeed 클래스
class CandleDatafeed {
  private _earliestDate: Date;
  private _data: CandleWithVolume[];
  private _broker: string;
  private _symbol: string;
  private _interval: string;
  private _isLoading: boolean;
  private _hasMoreData: boolean;
  
  constructor(broker: string, symbol: string, interval: string) {
    this._broker = broker;
    this._symbol = symbol;
    this._interval = interval;
    this._earliestDate = this._getInitialDate(interval);
    this._data = [];
    this._isLoading = false;
    this._hasMoreData = true;
  }
  
  private _getInitialDate(interval: string): Date {
    const now = new Date();
    const unit = interval.slice(-1).toLowerCase();
    
    switch (unit) {
      case 's': // 초봉: 1시간 전
        now.setHours(now.getHours() - 1);
        break;
      case 'm': // 분봉: 12시간 전
        now.setHours(now.getHours() - 12);
        break;
      case 'h': // 시간봉: 7일 전
        now.setDate(now.getDate() - 7);
        break;
      case 'd': // 일봉: 30일 전
        now.setDate(now.getDate() - 30);
        break;
      case 'w': // 주봉: 90일 전
        now.setDate(now.getDate() - 90);
        break;
      default: // 기본: 7일 전
        now.setDate(now.getDate() - 7);
    }
    
    return now;
  }
  
  async getBars(numberOfExtraBars: number): Promise<CandleWithVolume[]> {
    // 이미 로딩 중이거나 더 이상 데이터가 없으면 현재 데이터 반환
    if (this._isLoading || !this._hasMoreData) {
      console.log(`⏸️ [Datafeed] Skip loading (isLoading: ${this._isLoading}, hasMoreData: ${this._hasMoreData})`);
      return this._data;
    }

    this._isLoading = true;
    const previousLength = this._data.length;

    try {
      // interval을 밀리초로 변환
      const getIntervalMs = (interval: string): number => {
        const value = parseInt(interval);
        const unit = interval.slice(-1).toLowerCase();

        console.log("Candle Interval : " + interval);
        
        switch (unit) {
          case 's': return value * 1000;
          case 'm': return value * 60 * 1000;
          case 'h': return value * 60 * 60 * 1000;
          case 'd': return value * 24 * 60 * 60 * 1000;
          case 'w': return value * 7 * 24 * 60 * 60 * 1000;
          default: return 60 * 60 * 1000;
        }
      };

      console.log("this._earliestDate : " + this._earliestDate);

      console.log("getIntervalMs : " + getIntervalMs(this._interval));
      
      // 가장 오래된 날짜 계산 (무한 스크롤 시 왼쪽 끝 기준)
      const intervalMs = getIntervalMs(this._interval);
      let endDate: Date;
      
      if (this._data.length > 0) {
        // 기존 데이터가 있으면 가장 오래된(첫 번째) 캔들 시간 사용
        const firstCandleTime = Number(this._data[0].time);
        endDate = new Date(firstCandleTime * 1000);
        console.log("Using first candle time as endDate");
      } else {
        // 초기 로드시에는 현재 시간 + 1일 사용 (시차 보정)
        endDate = new Date();
        endDate.setDate(endDate.getDate() + 1);
        console.log("Using tomorrow as endDate (initial load)");
      }

      console.log("numberOfExtraBars : " + numberOfExtraBars);
      console.log("intervalMs * numberOfExtraBars : " + (intervalMs * numberOfExtraBars));
      console.log("endDate : " + endDate);
      
      const endTime = endDate.toISOString().slice(0, 19).replace('T', ' ');
      console.log("endTime : " + endTime);
      
      // API 호출
      const url = `${CANDLE_API_URL}/${this._broker}?symbol=${this._symbol}&interval=${this._interval}&end_time=${encodeURIComponent(endTime)}`;
      console.log(`[Datafeed] Fetching from: ${url}`);
      
      const token = SecureAuthService.getAccessToken();
      const response = await fetch(url, {
        method: "GET",
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });
      const data = await response.json();
      
      if (data.message === 'success' && data.candles && Array.isArray(data.candles)) {
        const newCandles: CandleWithVolume[] = data.candles;
        
        // 중복 제거
        const existingTimes = new Set(this._data.map(c => Number(c.time)));
        const uniqueNewCandles = newCandles.filter(c => !existingTimes.has(Number(c.time)));
        
        // 새 데이터를 앞에 추가하고 정렬
        this._data = [...uniqueNewCandles, ...this._data];
        this._data.sort((a, b) => Number(a.time) - Number(b.time));
        
        // 가장 오래된 날짜 업데이트
        if (this._data.length > 0) {
          this._earliestDate = new Date(Number(this._data[0].time) * 1000);
        }
        
        // 데이터가 증가하지 않았으면 더 이상 로드할 데이터가 없음
        if (this._data.length === previousLength) {
          this._hasMoreData = false;
          console.log('⚠️ [Datafeed] No more data available');
        }
        
        return this._data;
      } else {
        throw new Error(data.error || 'Invalid response format');
      }
    } catch (err) {
      console.error('[Datafeed] Failed to fetch data:', err);
      return this._data; // 실패 시 기존 데이터 반환
    } finally {
      this._isLoading = false;
    }
  }
  
  reset(broker: string, symbol: string, interval: string) {
    this._broker = broker;
    this._symbol = symbol;
    this._interval = interval;
    this._earliestDate = this._getInitialDate(interval);
    this._data = [];
    this._isLoading = false;
    this._hasMoreData = true;
  }
}

interface CandleChartProps {
  broker?: string;
  symbol?: string;
  interval?: string;
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
  const datafeedRef = useRef<CandleDatafeed | null>(null);
  const [candleData, setCandleData] = useState<CandleWithVolume[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // 실시간 체결가 구독
  const tradeData = useSharedTradeWebSocket(broker, symbol.toLowerCase());

  // broker나 symbol이 변경되면 데이터 초기화
  useEffect(() => {
    setCandleData([]);
    setIsLoading(true);
    setError(null);
    lastCandleRef.current = null; // ref도 초기화
    // datafeed 재생성
    datafeedRef.current = new CandleDatafeed(broker, symbol, interval);
  }, [broker, symbol, interval]);

  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        if (!datafeedRef.current) {
          datafeedRef.current = new CandleDatafeed(broker, symbol, interval);
        }
        
        // 초기 200개 바 로드
        const data = await datafeedRef.current.getBars(200);
        setCandleData(data);
      } catch (err) {
        console.error(`[CandleChart] Failed to load initial data:`, err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadInitialData();
  }, [broker, symbol, interval]);

  // 실시간 가격 업데이트 (마지막 캔들 정보를 ref로 관리)
  const lastCandleRef = useRef<CandleWithVolume | null>(null);

  useEffect(() => {
    if (!candleSeriesRef.current || !tradeData || !tradeData.price) {
      return;
    }

    const price = Number(tradeData.price);
    const quantity = Number(tradeData.quantity) || 0;
    if (isNaN(price)) return;

    // 마지막 캔들 정보 가져오기 (candleData가 업데이트되면 ref도 업데이트)
    if (candleData.length > 0) {
      const lastCandle = candleData[candleData.length - 1];
      // ref가 없거나 시간이 다르면 업데이트
      if (!lastCandleRef.current || lastCandleRef.current.time !== lastCandle.time) {
        lastCandleRef.current = { ...lastCandle };
      }
    }

    if (!lastCandleRef.current) return;

    const currentTime = Math.floor(Date.now() / 1000);
    
    // interval을 초로 변환
    const getIntervalSeconds = (interval: string): number => {
      const value = parseInt(interval);
      const unit = interval.slice(-1).toLowerCase();
      
      switch (unit) {
        case 's': return value;
        case 'm': return value * 60;
        case 'h': return value * 60 * 60;
        case 'd': return value * 24 * 60 * 60;
        default: return 60 * 60;
      }
    };
    
    const intervalSeconds = getIntervalSeconds(interval);
    const lastCandleTime = Number(lastCandleRef.current.time);
    const timeDiff = currentTime - lastCandleTime;
    
    // 같은 캔들 기간 내에 있는지 확인
    if (timeDiff < intervalSeconds) {
      // 기존 캔들 업데이트 (ref만 업데이트)
      const updatedCandle: CandleWithVolume = {
        time: lastCandleRef.current.time,
        open: lastCandleRef.current.open,
        high: Math.max(lastCandleRef.current.high, price),
        low: Math.min(lastCandleRef.current.low, price),
        close: price,
        volume: (lastCandleRef.current.volume || 0) + quantity,
      };
      
      // ref 업데이트
      lastCandleRef.current = updatedCandle;
      
      // 차트만 업데이트 (상태 업데이트 없음 - 리렌더링 방지)
      candleSeriesRef.current.update(updatedCandle);
      
      // volume 시리즈도 업데이트
      if (volumeSeriesRef.current) {
        volumeSeriesRef.current.update({
          time: updatedCandle.time,
          value: updatedCandle.volume || 0,
          color: (updatedCandle.close >= updatedCandle.open) ? upColor : downColor,
        });
      }
    } else {
      // 새 캔들 생성 (다음 기간으로 넘어감)
      const newCandleTime = (lastCandleTime + intervalSeconds) as Time;
      
      if (currentTime >= (newCandleTime as number)) {
        const newCandle: CandleWithVolume = {
          time: newCandleTime,
          open: price,
          high: price,
          low: price,
          close: price,
          volume: quantity,
        };
        
        // ref 업데이트
        lastCandleRef.current = newCandle;
        
        // 차트에 새 캔들 추가
        candleSeriesRef.current.update(newCandle);
        
        // volume 시리즈도 추가
        if (volumeSeriesRef.current) {
          volumeSeriesRef.current.update({
            time: newCandle.time,
            value: newCandle.volume || 0,
            color: upColor, // 새 캔들은 일단 상승색
          });
        }
        
        // state도 업데이트 (무한 스크롤 동기화)
        setCandleData(prev => [...prev, newCandle]);
      }
    }
  }, [tradeData, interval, candleData, upColor, downColor]);

  useEffect(() => {
    if (!chartContainerRef.current || candleData.length === 0) return;

    const chartWidth = typeof width === 'string' && width.endsWith('px')
      ? parseInt(width)
      : chartContainerRef.current.clientWidth;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: backgroundColor },
        textColor: textColor,
        panes: {
          separatorColor: '#2b2b43',
          separatorHoverColor: 'rgba(100, 100, 100, 0.3)',
          enableResize: true,
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
        lockVisibleTimeRangeOnResize: true,
      },
      crosshair: {
        mode: 0,
        vertLine: {
          width: 1,
          color: '#758696',
          style: 3,
          labelVisible: true,
        },
        horzLine: {
          width: 1,
          color: '#758696',
          style: 3,
          labelVisible: true,
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

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: upColor,
      downColor: downColor,
      borderVisible: false,
      wickUpColor: upColor,
      wickDownColor: downColor,
    });

    candlestickSeries.setData(candleData);

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: {
        type: 'volume',
      },
    }, 1);

    const volumeData = candleData.map(candle => ({
      time: candle.time,
      value: candle.volume || 0,
      color: (candle.close >= candle.open) ? upColor : downColor,
    }));
    
    volumeSeries.setData(volumeData);

    const volumePane = chart.panes()[1];
    if (volumePane) {
      volumePane.setHeight(Math.floor(height * 0.3));
    }

    // 마지막 30개 바만 보여주기
    chart.timeScale().setVisibleLogicalRange({
      from: Math.max(0, candleData.length - 30),
      to: candleData.length
    });

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
              <strong style="color: ${textColor};">${symbol.toUpperCase()}</strong>
              <span style="color: #888;">O</span> <strong style="color: ${candleColor};">${open}</strong>
              <span style="color: #888;">H</span> <strong style="color: ${candleColor};">${high}</strong>
              <span style="color: #888;">L</span> <strong style="color: ${candleColor};">${low}</strong>
              <span style="color: #888;">C</span> <strong style="color: ${candleColor};">${close}</strong>
            </div>
          `;
        } else {
          legendRef.current.innerHTML = `
            <div style="color: ${textColor};">
              <strong>${symbol.toUpperCase()}</strong>
            </div>
          `;
        }
      };
      
      chart.subscribeCrosshairMove(updateLegend);
      
      legendRef.current.innerHTML = `
        <div style="color: ${textColor};">
          <strong>${symbol}</strong>
        </div>
      `;
    }

    chartRef.current = chart;
    candleSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    // 무한 스크롤 구현 (실제 API 호출)
    chart.timeScale().subscribeVisibleLogicalRangeChange(logicalRange => {
      if (!logicalRange || !datafeedRef.current) return;
      
      if (logicalRange.from < 10) {
        // 추가 데이터 로드
        const numberBarsToLoad = Math.ceil(50 - logicalRange.from);
        console.log(`📍 [CandleChart] Near left edge, loading ${numberBarsToLoad} bars...`);
        
        // 비동기로 새로운 데이터 가져오기
        datafeedRef.current.getBars(numberBarsToLoad).then(newData => {
          // 로딩 딜레이 추가
          setTimeout(() => {
            if (candleSeriesRef.current && volumeSeriesRef.current) {
              candleSeriesRef.current.setData(newData);
              
              const volumeData = newData.map(candle => ({
                time: candle.time,
                value: candle.volume || 0,
                color: (candle.close >= candle.open) ? upColor : downColor,
              }));
              volumeSeriesRef.current.setData(volumeData);
              
              console.log(`✅ [CandleChart] Loaded ${numberBarsToLoad} additional bars, total: ${newData.length}`);
            }
          }, 250);
        }).catch(err => {
          console.error(`❌ [CandleChart] Failed to load more data:`, err);
        });
      }
    });

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
      chart.timeScale().subscribeVisibleLogicalRangeChange(() => {}); // 구독 해제
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [candleData, height, width, backgroundColor, textColor, upColor, downColor, symbol, broker, interval]);

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