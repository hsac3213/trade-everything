# Reference : https://apiportal.koreainvestment.com/apiservice-summary
API_URL = "https://openapi.koreainvestment.com:9443"
WS_URL = "ws://ops.koreainvestment.com:21000"

# https://www.truefriend.com/main/bond/research/_static/TF03ca050001.jsp
# [ 거래 가능 시간 ]
# 주간거래(ATS)
DAY_MARKET_TIME = [ "10:00", "18:00" ]
# 프리마켓
PRE_MARKET_TIME = [ "18:00", "23:30" ]
# 정규장
MAIN_MARKET_TIME = [ "23:30", "06:00" ]
# 애프터마켓
AFTER_MARKET_TIME = [ "06:00", "07:00" ]
# 애프터마켓 연장 신청 시(서머타임 동일)
EXTENDED_AFTER_MARKET_TIME = [ "07:00", "09:00" ]

# [ 서머타임 ]
# 주간거래(ATS)
#DAY_MARKET_TIME = [ "10:00", "17:00" ]
# 프리마켓
#PRE_MARKET_TIME = [ "17:00", "22:30" ]
# 정규장
#MAIN_MARKET_TIME = [ "22:30", "05:00" ]
# 애프터마켓
#AFTER_MARKET_TIME = [ "05:00", "06:00" ]

# 컬럼 이름을 한국어로 변환
# -> 항상 API 문서와 같은지 크로스체크할 것!
# Reference : https://github.com/koreainvestment/open-trading-api
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

    # 웹소켓 실시간/지연 체결가
    "RSYM": "실시간종목코드",
    # ^^ 코드에 누락된 컬럼 추가
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
    "MTYP": "시장구분",

    # 웹소켓 실시간 체결통보
    "CUST_ID": "고객 ID",
    "ACNT_NO": "계좌번호",
    "ODER_NO": "주문번호",
    "OODER_NO": "원주문번호",
    "SELN_BYOV_CLS": "매도매수구분",
    "RCTF_CLS": "정정구분",
    "ODER_KIND2": "주문종류2",
    "STCK_SHRN_ISCD": "주식 단축 종목코드",
    "CNTG_QTY": "체결수량",
    "CNTG_UNPR": "체결단가",
    "STCK_CNTG_HOUR": "주식 체결 시간",
    "RFUS_YN": "거부여부",
    "CNTG_YN": "체결여부",
    "ACPT_YN": "접수여부",
    "BRNC_NO": "지점번호",
    "ODER_QTY": "주문 수량",
    "ACNT_NAME": "계좌명",
    "CNTG_ISNM": "체결종목명",
    "ODER_COND": "해외종목구분",
    "DEBT_GB": "담보유형코드",
    "DEBT_DATE": "담보대출일자",
    "START_TM": "분할매수/매도 시작시간",
    "END_TM": "분할매수/매도 종료시간",
    "TM_DIV_TP": "시간분할타입유형",
}

# 거래 시간 전처리
from datetime import datetime, timedelta, time, date
def preprocess_market_time(market_time):
    #return datetime.strptime(market_time[0], "%H:%M").time(), datetime.strptime(market_time[1], "%H:%M").time()
    start_str, end_str = market_time
    today = date.today()
    
    start_time = datetime.strptime(start_str, "%H:%M").time()
    end_time = datetime.strptime(end_str, "%H:%M").time()
    
    start_dt = datetime.combine(today, start_time)
    end_dt = datetime.combine(today, end_time)
    
    # 자정 이후 시각 처리
    if end_dt < start_dt:
        end_dt += timedelta(days=1)
        
    return start_dt, end_dt

def check_market_time(market_time):
    market_time_dt = preprocess_market_time(market_time)

    print(market_time_dt[0])
    print(market_time_dt[1])

    if market_time_dt[0] <= datetime.now() < market_time_dt[1]:
        return True
    return False

#DAY_MARKET_DT = preprocess_market_time(DAY_MARKET_TIME)
#PRE_MARKET_DT = preprocess_market_time(PRE_MARKET_TIME)
#MAIN_MARKET_DT = preprocess_market_time(MAIN_MARKET_TIME)
#AFTER_MARKET_DT = preprocess_market_time(AFTER_MARKET_TIME)
#EXTENDED_AFTER_MARKET_DT = preprocess_market_time(EXTENDED_AFTER_MARKET_TIME)