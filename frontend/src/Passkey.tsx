import {
  startRegistration,
  startAuthentication,
} from '@simplewebauthn/browser';

// Python FastAPI 서버 주소
const API_URL = 'http://192.168.0.21:8000';

// ==================
// 1. 키 등록 (Registration)
// ==================
export const handleRegister = async (username: string) => {
  try {
    // Get registration options from server
    const resp = await fetch(`${API_URL}/register/begin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username }),
    });
    
    let options = await resp.json();
    
    // If the server returns a JSON string instead of an object, parse it
    if (typeof options === 'string') {
      console.log('Options is a string, parsing...');
      options = JSON.parse(options);
    }
    
    console.log('Parsed options:', options);
    console.log('Challenge:', options.challenge);
    
    // Start registration with WebAuthn
    const attResp = await startRegistration(options);
    
    // Send attestation response to server for verification
    const verificationResp = await fetch(`${API_URL}/register/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username,
        attestationResponse: attResp,
      }),
    });
    
    const verificationJSON = await verificationResp.json();
    
    if (verificationJSON.verified) {
      return { success: true, message: 'Registration successful!' };
    } else {
      return { success: false, message: 'Registration failed!' };
    }
  } catch (error) {
    return { 
      success: false, 
      message: `Error: ${error instanceof Error ? error.message : String(error)}` 
    };
  }
};

// ==================
// 2. 로그인 (Authentication)
// ==================
export const handleLogin = async (username: string) => {
  try {
    // Get authentication options from server
    const resp = await fetch(`${API_URL}/login/begin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username }),
    });
    
    let options = await resp.json();
    
    // If the server returns a JSON string instead of an object, parse it
    if (typeof options === 'string') {
      console.log('Options is a string, parsing...');
      options = JSON.parse(options);
    }
    
    console.log('Parsed authentication options:', options);
    
    // Start authentication with WebAuthn
    const asseResp = await startAuthentication(options);
    
    // Send assertion response to server for verification
    const verificationResp = await fetch(`${API_URL}/login/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username,
        assertionResponse: asseResp,
      }),
    });
    
    const verificationJSON = await verificationResp.json();
    
    if (verificationJSON.verified) {
      return { success: true, message: 'Login successful!' };
    } else {
      return { success: false, message: 'Login failed!' };
    }
  } catch (error) {
    return { 
      success: false, 
      message: `Error: ${error instanceof Error ? error.message : String(error)}` 
    };
  }
};