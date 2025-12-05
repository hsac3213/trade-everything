# Trade Everything

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.118-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![FIDO2](https://img.shields.io/badge/FIDO2-Passkey-FFCC00?style=for-the-badge&logo=fido-alliance&logoColor=black)
![GitHub Copilot](https://img.shields.io/badge/GitHub_Copilot-Enabled-000000?style=for-the-badge&logo=github-copilot&logoColor=white)

## 웹기반 통합 금융상품 거래 시스템

---
# 개요
Trade Everything은 각 증권사별 매매 프로그램(HTS) 설치 없이 한번의 로그인으로 주식과 암호화폐의 거래 및 자산 조회가 가능한 웹 어플리케이션입니다.

---

# 주요 기능
- 비밀번호를 사용하지 않는 passkey 기반 로그인 방식으로 보안 강화
- 금융상품 과거 시세 조회(캔들 차트)
- 금융상품 실시간 시세 조회(호가, 체결가)
    - 호가 클릭시 자동으로 주문 가격에 기입됨
- 금융상품 미체결 주문 조회
- 금융상품 지정가 주문, 주문 취소
    - 다른 플랫폼에서 제출한 미체결 주문도 (일괄)취소 가능
    - 다른 플랫폼에서 제출한 주문도 실시간으로 목록에 추가됨
- 보유 자산 목록 통합 조회
- 금융상품 즐겨찾기 추가/조회
---
# Demo Video
![Demo](./images/Demo_Video.gif)
---
# To-do List
- [ ] 시장가 주문, 서버 예약 주문 등의 주문 옵션 추가
- [ ] 스크립트 실행 기능 추가(스크립트에 따라 자동으로 매매 및 리스크 관리)
- [ ] 
---
# References
한국투자증권 OpenAPI 공식 샘플 코드<br>
https://github.com/koreainvestment/open-trading-api<br>
한국투자증권 웹소켓 예제 코드<br>
https://wikidocs.net/book/7847<br>
Binance 웹소켓 request security 코드<br>
https://developers.binance.com/docs/binance-spot-api-docs/websocket-api/request-security<br>
---

# TradingView
TradingView Lightweight Charts™
Copyright (с) 2025 TradingView, Inc. https://www.tradingview.com/

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file(or License page on the website) for details.

### Third-Party Licenses

This project uses various open-source dependencies:
- **MIT License** (174 packages): Most permissive, allows commercial use
- **Apache-2.0** (15 packages): Permissive with patent grant
- **MPL-2.0** (3 packages): Weak copyleft, used as library
- **ISC** (15 packages): Functionally equivalent to MIT
- **BSD variants** (8 packages): Permissive licenses

For detailed license information, see:
- [THIRD_PARTY_LICENSES.md](frontend/THIRD_PARTY_LICENSES.md) - Complete dependency list
- [NOTICES](NOTICES) - Special license notices

### License Compliance

✅ All dependencies are compatible with commercial distribution<br>
✅ Apache-2.0 and MPL-2.0 license texts preserved<br>
✅ TradingView attribution displayed in application
