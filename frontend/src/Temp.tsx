import CandleChart from './CandleChart';
import './App.css';

function App() {
  return (
    <div className="App">
      <h1 style={{ textAlign: 'center', color: '#ffffff', marginBottom: '20px' }}>
        캔들 차트 예제
      </h1>

      {/* 기본 설정으로 캔들 차트 사용 (임의 데이터 생성) */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '40px' }}>
        <CandleChart />
      </div>
      
      {/*커스텀 설정으로 캔들 차트 사용*/}
      {/*
      <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '40px' }}>
        <h2 style={{ textAlign: 'center', color: '#ffffff', marginBottom: '20px' }}>
          커스텀 색상 차트
        </h2>
        <CandleChart 
          height={400}
          upColor="#4caf50"
          downColor="#f44336"
          backgroundColor="#0a0a0a"
        />
      </div>
      */}
    </div>
  );
}

export default App;
