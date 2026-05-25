"""
하이버 주문서 파싱 모듈
"""
import pandas as pd


def parse_hyber_orders(file_path):
    """
    하이버 주문서를 파싱하여 통합주문서 형식으로 변환
    
    Args:
        file_path (str): 하이버 주문서 파일 경로 (실제로는 .xlsx 파일)
        
    Returns:
        tuple: (변환된 DataFrame, 원본 DataFrame)
    """
    # 하이버 파일은 .csv 확장자지만 실제로는 엑셀 파일
    # dtype=object로 읽어서 날짜가 자동 변환되지 않도록 함
    df_original = pd.read_excel(file_path, dtype=object)
    
    # C,S,T,U,V,K,L,P,W 열 매핑
    # C(2): 주문번호, S(18): 수령자명, T(19): 수령자연락처, U(20): 우편번호, V(21): 배송지
    # K(10): 상품명, L(11): 옵션정보, P(15): 수량, W(22): 배송시 요청사항
    
    df_converted = pd.DataFrame({
        '주문번호': df_original.iloc[:, 2].fillna('').astype(str),      # C열
        '받는사람': df_original.iloc[:, 18].fillna('').astype(str),     # S열
        '전화번호1': df_original.iloc[:, 19].fillna('').astype(str),    # T열
        '우편번호': df_original.iloc[:, 20].fillna('').astype(str),     # U열
        '주소': df_original.iloc[:, 21].fillna('').astype(str),         # V열
        '상품명1': df_original.iloc[:, 10].fillna('').astype(str),      # K열
        '상품상세1': df_original.iloc[:, 11].fillna('').astype(str),    # L열
        '내품수량1': df_original.iloc[:, 15],                # P열
        '배송메시지': df_original.iloc[:, 22].fillna('').astype(str),   # W열
        '수량(A타입)': 1                                     # 고정값
    })
    
    # NaN을 빈 문자열로 변환
    df_converted = df_converted.fillna('')
    
    return df_converted, df_original
