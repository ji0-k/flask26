from LMS.service.MemberService import MemberService
from LMS.service.ScoreService import ScoreService
from LMS.service.BoardService import BoardService
#    최상위       파일명(모듈)          클래스명

# 다른 패키지에서 import *로 처리 가능
__all__ = ['MemberService', 'ScoreService', 'BoardService']

# service 파일 : 데이터의 통로

# 1.객체를 DB에 저장하기
# Serialization/Persistence
# 메모리에 떠있는 객체데이터를 DB라는 영구적인 저장소에 넣는 과정
# 프로그램이 종료되어도 데이터가 사라지지 않게 보호
# INSERT / UPDATE 쿼리 실행

# 2.DB 데이터를 불러와서 객체화 하기
# Deserialization/Mapping
# DB에 텍스트/숫자 형태의 데이터를 꺼내와서 파이썬에서 자유롭게 쓸 수 있는 객체형태로
# SELECT 쿼리 실행 후 결과를 클래스 생성자에 넣어 인스턴스화 (찍어내기)
# 파이썬 문법으로 데이터를 쉽게 다루기 위함

# 보통 이런 설계를 DAO(Data Access Object) 또는 Repository 패턴
# 비즈니스 로직(성적 계산 등)과 데이터 저장 로직(DB 쿼리)을 분리하면
# 나중에 DB가 바뀌거나 테이블 구조가 변해도 해당 service 파일만
# 수정하면 되기 때문에 아주 깔끔한 설계 방식
