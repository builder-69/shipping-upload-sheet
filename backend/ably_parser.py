"""
에이블리 주문서 파싱 모듈
"""
import pandas as pd


def parse_ably_orders(file_path):
    """
    에이블리 주문서를 파싱하여 통합주문서 형식으로 변환
    
    Args:
        file_path (str): 에이블리 주문서 파일 경로
        
    Returns:
        tuple: (변환된 DataFrame, 원본 DataFrame)
    """
    # 에이블리는 2번째 시트(인덱스 1)가 주문 내용
    # dtype=object로 읽어서 날짜가 자동 변환되지 않도록 함
    df_original = pd.read_excel(file_path, sheet_name=1, dtype=object)
    
    # C,N,O,P,Q,G,I,J,R 열 매핑
    # C(2): 주문번호, N(13): 수취인명, O(14): 수취인 연락처, P(15): 우편번호, Q(16): 배송지 주소
    # G(6): 상품명, I(8): 옵션 정보, J(9): 수량, R(17): 배송 메모
    
    df_converted = pd.DataFrame({
        '주문번호': df_original.iloc[:, 2].astype(str),      # C열
        '받는사람': df_original.iloc[:, 13].astype(str),     # N열
        '전화번호1': df_original.iloc[:, 14].astype(str),    # O열
        '우편번호': df_original.iloc[:, 15].astype(str),     # P열
        '주소': df_original.iloc[:, 16].astype(str),         # Q열
        '상품명1': df_original.iloc[:, 6].astype(str),       # G열
        '상품상세1': df_original.iloc[:, 8].astype(str),     # I열
        '내품수량1': df_original.iloc[:, 9],                 # J열
        '배송메시지': df_original.iloc[:, 17].astype(str),   # R열
        '수량(A타입)': 1                                     # 고정값
    })
    
    # NaN을 빈 문자열로 변환
    df_converted = df_converted.fillna('')
    
    return df_converted, df_original
