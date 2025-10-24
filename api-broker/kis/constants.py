API_URL = "https://openapi.koreainvestment.com:9443"
WS_URL = "ws://ops.koreainvestment.com:21000"

# 컬럼 이름을 한국어로 변환
COLUMN_TO_KOR_DICT = {
    # 웹소켓 실시간 호가
    "rsym": "실시간종목코드",
    "symb": "종목코드",
    "zdiv": "소숫점자리수",
    "xymd": "현지일자",
    "xhms": "현지시간",
    "kymd": "한국일자",
    "khms": "한국시간",
    "bvol": "매수총잔량",
    "avol": "매도총잔량",
    "bdvl": "매수총잔량대비",
    "advl": "매도총잔량대비",
    "pbid1": "매수호가1",
    "pask1": "매도호가1",
    "vbid1": "매수잔량1",
    "vask1": "매도잔량1",
    "dbid1": "매수잔량대비1",
    "dask1": "매도잔량대비1",

    # 웹소켓 실시간 체결가
    "SYMB": "종목코드",
    "ZDIV": "수수점자리수",
    "TYMD": "현지영업일자",
    "XYMD": "현지일자",
    "XHMS": "현지시간",
    "KYMD": "한국일자",
    "KHMS": "한국시간",
    "OPEN": "시가",
    "HIGH": "고가",
    "LOW": "저가",
    "LAST": "현재가",
    "SIGN": "대비구분",
    "DIFF": "전일대비",
    "RATE": "등락율",
    "PBID": "매수호가",
    "PASK": "매도호가",
    "VBID": "매수잔량",
    "VASK": "매도잔량",
    "EVOL": "체결량",
    "TVOL": "거래량",
    "TAMT": "거래대금",
    "BIVL": "매도체결량",
    "ASVL": "매수체결량",
    "STRN": "체결강도",
    "MTYP": "시장구분"
}