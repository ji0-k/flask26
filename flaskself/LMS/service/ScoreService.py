from LMS.common import Session
from LMS.domain import Score

class ScoreService:

    @classmethod # 클래스 메서드: Score.load() 이렇게 호출
    def load(cls): #접속 테스트용, 테이블 데이터 개수를 확인

        #1. DB연결객체 가져오기 ( Session은 DB연결 관리 클래스)
        conn = Session.get_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM scores")
                #                                       scores테이블에서
                #테이블전체 행을세서 cnt에 넣어라
                count = cursor.fetchone()['cnt']
                print(f"현재 등록 DB :{count}")

        except Exception as e:
            print(e)
        finally:
            conn.close()

    @classmethod #클래스 메서드 Score.run()으로 호출
    def run(cls):
        cls.load() # DB연결 테스트 (scores 테이블 데이터 개수)

        if not Session.is_login():
            print("로그인 후 이용 가능합니다.")
            return

        member = Session.login_member #현재 Session에들어가있는 회원정보 가져오기

        while True:
            print("\n====== 성적 관리 시스템 ======")

            # 1. 관리자/매니저 메뉴
            if member.role in ("manager", "admin"):
                print("1. 학생 성적 입력/수정")

            # 2. 공통 메뉴
            print("2. 내 성적 조회")

            # 3. 관리자 전용 메뉴
            if member.role == "admin":
                print("3. 전체 성적 현황 (JOIN)")

            print("0. 뒤로가기")

            sel = input(">>> ")
            if sel == "1" and member.role in ("manager", "admin"):
                cls.add_score()
            elif sel == "2":
                cls.view_my_score()
            elif sel == "3" and member.role == "admin":
                cls.view_all()
            elif sel == "0":
                break

    @classmethod
    # 무결성 FK관계를 확인하고 객체지향 (Score객체)계산로직을 처리한뒤 , insert 또는 UPDATE 로직
    def add_score(cls):  # admin이나 manager 권한 가진 사용자만 입력 가능
        # 1. 대상 학생 식별을위한 회원 아이디 uid 입력받음
        target_uid = input("성적 입력할 학생 아이디(uid): ")
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. 학생 존재 확인 (pk -> fk 에 대한 문제 해결용)
                #  부모테이블에 자료가 있어야 자식 테이블에 자료를 넣는다.
                cursor.execute("SELECT id, name FROM members WHERE uid = %s", (target_uid,))
                # 특정 조건을 만족하는 데이터를 조회(SELECT)
                # cursor DB SQL명령 전달 결과 받아오는 객체
                # SELECT id, name FROM members: 멤버스테이블에 id와 name만 가져와
                # WHERE uid = %s (조건절) : uid컬럼 값이 %s위치에 들어갈 값과 일치하는 행 row만 찾아
                # 찾은 타겟 uid (target_uid,) %s자리에 채워 넣을 변수 , 튜플형태로 전달 ,


                student = cursor.fetchone()  # members테이블에 uid가 있으면 딕셔너리 / 없으면 None반환

                if not student:  # false일때
                    print(f"'{target_uid}' 학생을 찾을 수 없습니다.")
                    return  # 객체가 있으면 아래 문 실행

                # 2. 점수 입력
                kor = int(input("국어: "))
                eng = int(input("영어: "))
                math = int(input("수학: "))

                # 3. 데이터 전용 그릇 Score 객체를 생성 (여기서 파이썬의 @property가 계산됨)
                temp_score = Score(member_id=student['id'], kor=kor, eng=eng, math=math)

                # 4. DB 저장 (객체의 프로퍼티 값을 SQL에 전달)
                cursor.execute("SELECT id FROM scores WHERE member_id = %s", (student['id'],))

                # 학생의 점수가 있으면????
                if cursor.fetchone():  # 있으면 true 없으면 false
                    # UPDATE 로직
                    sql = """
                          UPDATE scores \
                          SET korean=%s, \
                              english=%s, \
                              math=%s, \
                              total=%s, \
                              average=%s, \
                              grade=%s
                          WHERE member_id = %s \
                          """
                    # 객체의 프로퍼티(temp_score.total 등)를 사용합니다.
                    cursor.execute(sql, (
                        temp_score.kor, temp_score.eng, temp_score.math,
                        temp_score.total, temp_score.avg, temp_score.grade,
                        student['id']
                    ))
                else:  # 기존에 성적이 없으면 실행 문
                    # INSERT 로직
                    sql = """
                          INSERT INTO scores (member_id, korean, english, math, total, average, grade)
                          VALUES (%s, %s, %s, %s, %s, %s, %s) \
                          """
                    cursor.execute(sql, (
                        student['id'], temp_score.kor, temp_score.eng, temp_score.math,
                        temp_score.total, temp_score.avg, temp_score.grade
                    ))

                conn.commit()  # db에 저장
                print(f"{student['name']} 학생의 성적 저장 완료 (객체 계산 방식)")
        finally:
            conn.close()

    @classmethod
    def view_my_score(cls):
        member = Session.login_member  # 로그인한 member 객체
        conn = Session.get_connection()  # db연결 객체
        try:
            with conn.cursor() as cursor:  # 연결 성공시 true
                # 로그인한 사람의 PK(id)로 성적 조회
                sql = "SELECT * FROM scores WHERE member_id = %s"
                cursor.execute(sql, (member.id,))
                data = cursor.fetchone()  # date에는 member db 정보가 담김

                if data:  # 데이터가 있으면
                    s = Score.from_db(data)  # dict 타입의 객체를 s에 넣음
                    # 도메인 클래스의 __init__에는 uid 정보가 없으므로 세션 정보를 활용해 출력
                    cls.print_score(s, member.uid)  # 콘솔에 보기 좋게 출력!!
                else:
                    print("등록된 성적이 없습니다.")
        finally:
            conn.close()

    @classmethod
    def print_score(cls, s, uid):  # 개인성적 출력과 전체 성적 출력도 가능(메서드 : 동작 -> 재활용가능)
        # 도메인 모델(Score)에 계산 로직(@property)이 있으므로 s.total, s.avg 등을 그대로 사용
        print(
            f"ID:{uid:<10} | "
            f"국어:{s.kor:>3} 영어:{s.eng:>3} 수학:{s.math:>3} | "
            f"총점:{s.total:>3} 평균:{s.avg:>5.2f} | 등급 : {s.grade}"
        )

        @classmethod
        def view_all(cls):
            print("\n[전체 성적 목록 - JOIN 결과]")
            conn = Session.get_connection()
            try:
                with conn.cursor() as cursor:
                    # members와 scores를 JOIN하여 아이디(uid)와 성적을 함께 가져옴
                    sql = """
                          SELECT m.uid, s.* \
                          FROM scores s \
                                   JOIN members m ON s.member_id = m.id \
                          """
                    cursor.execute(sql)
                    datas = cursor.fetchall()  # .fatchall()은 모든값

                    for data in datas:
                        s = Score.from_db(data)  # dict 타입을 객체로 만듬
                        cls.print_score(s, data['uid'])  # 출력용 메서드에 주입
            finally:
                conn.close()