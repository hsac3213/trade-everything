/**
 * 보안 강화 인증 서비스
 * JWT + 메모리 기반 토큰 관리 + 자동 갱신 + Passkey 지원
 */
import { API_URL } from '../Common/Constants'

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserInfo {
  user_id: number;
  username: string;
}

export interface SessionInfo {
  ip: string;
  user_agent: string;
  created_at: string;
}

export class SecureAuthService {
  // 메모리에만 토큰 저장 (XSS 방지)
  private static accessToken: string | null = null;
  private static refreshToken: string | null = null;
  private static refreshTimer: number | null = null;

  /**
   * Passkey 로그인 (토큰 저장 포함)
   */
  static async loginWithPasskey(username: string): Promise<void> {
    // PasskeyAuth에서 로그인 수행
    const { handlePasskeyLogin } = await import('./PasskeyAuth');
    const result = await handlePasskeyLogin(username);

    if (!result.success || !result.tokens) {
      throw new Error(result.message);
    }

    // 토큰 저장 및 자동 갱신 시작
    this.setTokens(result.tokens.access_token, result.tokens.refresh_token);
    this.startAutoRefresh(result.tokens.expires_in);

    console.log("JWT : ", result.tokens.access_token);
  }

  /**
   * Passkey 등록
   */
  static async registerWithPasskey(username: string): Promise<{ success: boolean; message: string }> {
    const { handlePasskeyRegister } = await import('./PasskeyAuth');
    return await handlePasskeyRegister(username);
  }

  /**
   * 로그아웃 (현재 디바이스만)
   */
  static async logout(): Promise<void> {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearTokens();
    }
  }

  /**
   * 모든 디바이스에서 로그아웃
   */
  static async logoutAllDevices(): Promise<void> {
    try {
      await fetch(`${API_URL}/auth/logout-all`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout all error:', error);
    } finally {
      this.clearTokens();
    }
  }

  /**
   * 토큰 갱신
   */
  static async refreshAccessToken(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ refresh_token: this.refreshToken })
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data: TokenResponse = await response.json();
      this.setTokens(data.access_token, data.refresh_token);

      console.log('✅ Token refreshed successfully');
      console.log(data.access_token);
    } catch (error) {
      console.error('❌ Token refresh error:', error);
      // 갱신 실패 시 로그아웃
      this.clearTokens();
      throw error;
    }
  }

  /**
   * 현재 사용자 정보 조회
   */
  static async getMe(): Promise<UserInfo> {
    const response = await fetch(`${API_URL}/auth/me`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user info');
    }

    return await response.json();
  }

  /**
   * 활성 세션 목록 조회
   */
  static async getActiveSessions(): Promise<SessionInfo[]> {
    const response = await fetch(`${API_URL}/auth/sessions`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error('Failed to fetch sessions');
    }

    return await response.json();
  }

  /**
   * 토큰 설정
   */
  private static setTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
  }

  /**
   * 토큰 제거 및 타이머 정리
   */
  private static clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;

    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Access Token 가져오기
   */
  static getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * 인증 여부 확인
   */
  static isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  /**
   * 인증 헤더 생성
   */
  static getAuthHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json'
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    return headers;
  }

  /**
   * 자동 토큰 갱신 시작
   * 토큰 만료 2분 전에 갱신
   */
  private static startAutoRefresh(expiresIn: number): void {
    // 기존 타이머 정리
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }

    // 만료 2분 전에 갱신 (expiresIn은 초 단위)
    const refreshInterval = (expiresIn - 120) * 1000;

    if (refreshInterval > 0) {
      this.refreshTimer = setInterval(async () => {
        try {
          await this.refreshAccessToken();
        } catch (error) {
          console.error('Auto refresh failed:', error);
          this.clearTokens();
          // 로그인 페이지로 리다이렉트 등 처리
          window.location.href = '/login';
        }
      }, refreshInterval);

      console.log(`🔄 Auto refresh enabled (interval: ${refreshInterval / 1000}s)`);
    }
  }

  /**
   * WebSocket 연결 시 인증 토큰 추가
   */
  static createAuthenticatedWebSocket(url: string): WebSocket {
    const token = this.getAccessToken();
    if (!token) {
      throw new Error('No access token available');
    }

    // URL에 토큰 추가
    const wsUrl = `${url}?token=${encodeURIComponent(token)}`;
    return new WebSocket(wsUrl);
  }
}

/**
 * Fetch API 래퍼 (자동 인증 헤더 추가)
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...SecureAuthService.getAuthHeaders(),
      ...options.headers
    },
    credentials: 'include'
  });

  // 401 에러 시 토큰 갱신 시도
  if (response.status === 401) {
    try {
      await SecureAuthService.refreshAccessToken();
      
      // 갱신 후 재시도
      return await fetch(url, {
        ...options,
        headers: {
          ...SecureAuthService.getAuthHeaders(),
          ...options.headers
        },
        credentials: 'include'
      });
    } catch (error) {
      // 갱신 실패 시 로그인 페이지로
      window.location.href = '/login';
      throw error;
    }
  }

  return response;
}

export default SecureAuthService;
