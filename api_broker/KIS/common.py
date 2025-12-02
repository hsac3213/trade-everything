from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

# https://github.com/koreainvestment/open-trading-api/blob/37a084dd9fd7b181ef3ff767c41a0472cfcee345/legacy/Sample01/kis_ovrseastk_ws.py#L238
def aes_decrypt(cipher_text, key, iv):
    """
    AES 복호화
    -> 실시간 체결통보
    """
    print(key)
    print(iv)

    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size))