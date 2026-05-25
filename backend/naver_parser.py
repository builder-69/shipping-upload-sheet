"""
네이버 스마트스토어 주문서 파싱 모듈
"""
import pandas as pd


def parse_naver_orders(file_path):
    """
    네이버 스마트스토어 주문서를 파싱하여 통합주문서 형식으로 변환
    
    Args:
        file_path (str): 네이버 주문서 파일 경로
        
    Returns:
        tuple: (변환된 DataFrame, 원본 DataFrame)
    """
    # 네이버 주문서는 2행부터 헤더 시작
    # dtype=object로 읽어서 날짜가 자동 변환되지 않도록 함
    df_original = pd.read_excel(file_path, header=1, dtype=object)
    
    # D열(3) ~ L열(11) 매핑
    # D: 주문번호, E: 수취인명, F: 수취인연락처1, G: 우편번호, H: 통합배송지
    # I: 상품명, J: 옵션정보, K: 수량, L: 배송메세지
    
    df_converted = pd.DataFrame({
        '주문번호': df_original.iloc[:, 3].astype(str),      # D열
        '받는사람': df_original.iloc[:, 4].astype(str),      # E열
        '전화번호1': df_original.iloc[:, 5].astype(str),     # F열
        '우편번호': df_original.iloc[:, 6].astype(str),      # G열
        '주소': df_original.iloc[:, 7].astype(str),          # H열
        '상품명1': df_original.iloc[:, 8].astype(str),       # I열
        '상품상세1': df_original.iloc[:, 9].astype(str),     # J열
        '내품수량1': df_original.iloc[:, 10],                # K열
        '배송메시지': df_original.iloc[:, 11].astype(str),   # L열
        '수량(A타입)': 1                                     # 고정값
    })
    
    # NaN을 빈 문자열로 변환
    df_converted = df_converted.fillna('')
    
    return df_converted, df_original
