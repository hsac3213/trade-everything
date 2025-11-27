-- 데이터베이스 스키마 생성
\c tedb

-- ==========================================
-- 1. 사용자 테이블
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);

-- ==========================================
-- 2. Passkey Credentials 테이블
-- ==========================================
CREATE TABLE IF NOT EXISTS passkey_credentials (
    credential_id VARCHAR(500) PRIMARY KEY,  -- Base64 encoded credential ID
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    public_key TEXT NOT NULL,                -- Base64 encoded public key
    sign_count BIGINT NOT NULL DEFAULT 0,    -- Sign count for replay attack prevention
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

CREATE INDEX idx_passkey_user_id ON passkey_credentials(user_id);

-- ==========================================
-- 3. 사용자 설정 테이블 (선택사항)
-- ==========================================
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    setting_type VARCHAR(50) NOT NULL,  -- 'favorites', 'preferences', 'api_keys' 등
    setting_data JSONB NOT NULL,        -- JSON 형식의 설정 데이터
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_settings_user_id ON user_settings(user_id);
CREATE INDEX idx_user_settings_type ON user_settings(user_id, setting_type);

-- 토큰 저장 데이터베이스
CREATE TABLE IF NOT EXISTS user_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    broker_name TEXT,
    token_name TEXT,
    token TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

CREATE INDEX idx_user_tokens_user_id ON user_tokens(user_id);

-- 캔들 데이터 (일봉, 시간봉 등 기록용)
DROP TABLE IF EXISTS candle_data;
CREATE TABLE candle_data (
    id SERIAL PRIMARY KEY,
    broker_name TEXT NOT NULL,           -- 거래소/브로커명 (예: 'Binance', 'KIS')
    symbol TEXT NOT NULL,                -- 심볼 (예: 'BTCUSDT', 'NVDA')
    interval VARCHAR(8) NOT NULL,        -- 봉 종류 (예: '1d', '1h', '15m', '5m')
    open_time TIMESTAMP NOT NULL,        -- 봉 시작 시각 (UTC)
    close_time TIMESTAMP NOT NULL,       -- 봉 종료 시각 (UTC)
    open NUMERIC(24,8) NOT NULL,         -- 시가
    high NUMERIC(24,8) NOT NULL,         -- 고가
    low NUMERIC(24,8) NOT NULL,          -- 저가
    close NUMERIC(24,8) NOT NULL,        -- 종가
    volume NUMERIC(32,12) NOT NULL,      -- 거래량
    quote_volume NUMERIC(32,12),         -- 거래대금 (선택)
    trade_count INTEGER,                 -- 거래 건수 (선택)
    taker_buy_base_asset_volume NUMERIC(32,12),
    taker_buy_quote_asset_volume NUMERIC(32,12),
    inserted_at TIMESTAMP DEFAULT now(), -- 기록 시각
    UNIQUE (broker_name, symbol, interval, open_time)
);

-- 조회 성능 향상을 위한 인덱스
CREATE INDEX idx_candle_broker_symbol_interval ON candle_data (broker_name, symbol, interval);
CREATE INDEX idx_candle_symbol_interval_time ON candle_data (symbol, interval, open_time DESC);
CREATE INDEX idx_candle_open_time ON candle_data (open_time DESC);

-- 테이블 소유자 변경
ALTER TABLE candle_data OWNER TO teadmin;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO teadmin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO teadmin;
GRANT USAGE ON SCHEMA public TO teadmin;

-- DB 권한 부여
GRANT ALL PRIVILEGES ON DATABASE tedb TO teuser;
GRANT ALL PRIVILEGES ON SCHEMA public TO teuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO teuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO teuser;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO teuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO teuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO teuser;