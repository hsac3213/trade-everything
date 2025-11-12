-- 데이터베이스 스키마 생성

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
    tokens_data JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

CREATE INDEX idx_user_tokens_user_id ON user_tokens(user_id);