class Score:
    # 1. 생성자 : 새로운 성적 객체를 만들때 실행되는 함수의 초기값 설정
    def __init__(self, member_id, kor, eng, math, id = None):
        self.id = id # scores 테이블의 PK,
        self.member_id = member_id # members테이블의 id와 연결된 FK
        self.kor = kor
        self.eng = eng
        self.math = math
        # id는 DB에서 자동생성되므로 기본값 None (나중에 DB에 저장되면 생김)

    # 파이썬 계산 프로퍼티 ( 메서드 지만 변수처럼 써먹는다)
    # 예: score.total() 대신 score.total 로 사용 가능
    @property
    def total(self):
        return self.kor + self.eng + self.math

    @property
    def average(self):
        return (self.kor + self.eng + self.math) / 3

    @property
    def grade(self):
        average = self.average  # 위에서 만든 average 프로퍼티 사용
        if average >= 90:
            return "A"
        elif average >= 80:
            return "B"
        elif average >= 70:
            return "C"
        elif average >= 60:
            return "D"
        else:
            return "F"

    # @classmethod: 클래스 자체에서 호출하는 메서드
    # Score.from_db(row) 이런 식으로 사용
    @classmethod
    def from_db(cls,row:dict):
        # DB딕셔너리에서 member_id 기반으로 객체 생성
        if not row : return None
        # row가 비어있으면 None 반환 (데이터가 없는 경우)

        # cls는 Score 클래스 자신을 의미
        # cls(...)는 Score(...)와 같음 = 새로운 Score 객체 생성
        return cls(
            id = row.get("id"),
            member_id = row.get("member_id"),
            kor = int(row.get("kor",0)),
            eng = int(row.get("eng",0)),
            math = int(row.get("math",0))
            # row.get("키", 기본값): 딕셔너리에서 "키"의 값을 가져오되, 없으면 기본값 사용
        )


