import {
  startRegistration,
  startAuthentication,
} from '@simplewebauthn/browser';
import { API_URL } from '../Common/Constants';

/**
 * Passkey 등록/로그인 결과
 */
export interface PasskeyResult {
  success: boolean;
  message: string;
  tokens?: {
    access_token: string;
    refresh_token: string;
    expires_in: number;
  };
}

// ==================
// 1. Passkey 등록 (Registration)
// ==================
export const handlePasskeyRegister = async (username: string): Promise<PasskeyResult> => {
  try {
    // 1. 서버에서 registration options 요청
    const resp = await fetch(`${API_URL}/auth/passkey/register/begin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    });
    
    if (!resp.ok) {
      const error = await resp.json();
      return { 
        success: false, 
        message: error.detail || 'Failed to start registration' 
      };
    }
    
    const options = await resp.json();
    
    console.log('📝 Registration options received:', options);
    
    // 2. WebAuthn으로 credential 생성 (사용자 인증 수행)
    const attResp = await startRegistration(options);
    
    console.log('✅ Credential created:', attResp);
    
    // 3. 서버에 attestation response 전송하여 검증
    const verificationResp = await fetch(`${API_URL}/auth/passkey/register/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        attestationResponse: attResp,
      }),
    });
    
    if (!verificationResp.ok) {
      const error = await verificationResp.json();
      return { 
        success: false, 
        message: error.detail || 'Registration verification failed' 
      };
    }
    
    const verificationJSON = await verificationResp.json();
    
    if (verificationJSON.verified) {
      return { 
        success: true, 
        message: 'Registration successful! You can now login with your passkey.' 
      };
    } else {
      return { 
        success: false, 
        message: 'Registration failed - verification unsuccessful' 
      };
    }
  } catch (error) {
    console.error('❌ Registration error:', error);
    return { 
      success: false, 
      message: `Error: ${error instanceof Error ? error.message : String(error)}` 
    };
  }
};

// ==================
// 2. Passkey 로그인 (Authentication)
// ==================
export const handlePasskeyLogin = async (username: string): Promise<PasskeyResult> => {
  try {
    // 1. 서버에서 authentication options 요청
    const resp = await fetch(`${API_URL}/auth/passkey/login/begin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    });
    
    if (!resp.ok) {
      const error = await resp.json();
      return { 
        success: false, 
        message: error.detail || 'Failed to start login' 
      };
    }
    
    const options = await resp.json();
    
    console.log('🔐 Authentication options received:', options);
    
    // 2. WebAuthn으로 인증 수행 (사용자가 passkey 사용)
    const asseResp = await startAuthentication(options);
    
    console.log('✅ Authentication response created:', asseResp);
    
    // 3. 서버에 assertion response 전송하여 검증 및 JWT 토큰 받기
    const verificationResp = await fetch(`${API_URL}/auth/passkey/login/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        assertionResponse: asseResp,
      }),
    });
    
    if (!verificationResp.ok) {
      const error = await verificationResp.json();
      return { 
        success: false, 
        message: error.detail || 'Login verification failed' 
      };
    }
    
    const tokens = await verificationResp.json();
    
    console.log('✅ Login successful, tokens received:', tokens);
    
    // 토큰을 반환하여 AuthService에서 저장하도록 함
    return { 
      success: true, 
      message: 'Login successful!',
      tokens: {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        expires_in: tokens.expires_in,
      }
    };
    
  } catch (error) {
    console.error('❌ Login error:', error);
    return { 
      success: false, 
      message: `Error: ${error instanceof Error ? error.message : String(error)}` 
    };
  }
};
