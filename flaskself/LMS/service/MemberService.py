# Member객체에 curd를 담당, 메뉴용 메서드 등...

from LMS.common import Session
from LMS.domain import Member

class MemberService:# 객체 생성 없이 기능만 제공 하므로 __inti__없음
    @classmethod
    def load(cls):  # db에 연결 테스트 및 초기화를 위해 클래스 자체에서 호출
        conn = Session.get_connection()  #Session관리소에서 DB연결객체를 받아옴

        try: #에러가 발생할 수 있는 코드를 안전하게 감싸다
            with conn.cursor() as cursor:  # DB작업을 수행할 '커서' 생성
                cursor.execute("select count(*) as cnt from members")
                #cursor.execute: SQL명령어를 DB에 전달함
                #             (Member 테이블에서 개수나온만큼 count변수에 넣어라)

                #count = cursor.fetchone()['cnt']  # dict 타입으로 나옴 cnt : 5
                # 장점: 코드가 짧고 간결합니다. 결과가 무조건 존재한다고 확신할 때 씁니다.
                # 단점: 만약 DB에 데이터가 하나도 없어서 fetchone()이 None을 반환하면,
                # None['cnt']를 참조하려다 에러(TypeError)가 발생하며 프로그램이 멈춥니다.
                #             .fetchone() 1개의 결과가 나올때 read one
                #             .fetchall() 여러개의 결과가 나올때 read all
                #             .fetchmany(3) 3개의 결과만 보고 싶을 때 (최상위3개)
                # [fetch 작동 원리]
                # cursor는 DB 결과를 가리키는 '손가락'과 같습니다.
                # fetch를 할 때마다 손가락이 다음 줄로 이동하며 데이터를 읽어옵니다.
                # 'count(*)' 쿼리는 결과가 무조건 1줄이므로 fetchone()이 가장 적절한 선택입니다

                result = cursor.fetchone()
                count = result['cnt']  # 딕셔너리에서 'cnt' 키의 숫자만 꺼냄
                # 장점: 중간에 'result'가 비어있는지(None인지) 검사할 수 있어 더 안전합니다.
                # 예: if result: count = result['cnt'] else: count = 0
                # 단점: 코드가 한 줄 더 늘어납니다.

                print(f"시스템에 현재 등록된 회원수는 {count}명 입니다. ")

        except Exception as e :  # 예외, 오류 발생 시 실행되는 블럭
            print(f"MemberService.load() 메서드 오류 발생: {e}")

        finally:  # 항상 출력되는 코드
            print("데이터베이스 접속 종료됨....")
            conn.close()

    # 1. @classmethod 사용 이유: 이 서비스는 "회원 한 명"의 데이터가 아니라
    #    "시스템 전체"의 데이터를 다룹니다. 따라서 객체를 만들(self) 필요 없이
    #    MemberService.load() 처럼 바로 호출하여 사용합니다.
    # 2. fetchone()의 리턴값: DictCursor를 사용 중이므로 결과는 항상 {'컬럼명': 값} 형태입니다.
    #    그래서 result['cnt']와 같이 키 값을 사용하여 데이터에 접근합니다.

    @classmethod
    def login(cls): # 객체 생성없이 실행하는 클래스 메서드
        print("\n[로그인]")
        uid = input("아이디: ") # 입력받음
        pw = input("비밀번호: ") # 입력받음

        conn = Session.get_connection() # DB연결 객체 가져오기

        try:
            with conn.cursor() as cursor:
                # 1. 아이디와 비밀번호가 일치하는 회원 조회
                sql = "SELECT * FROM members WHERE uid = %s AND password = %s"
                # %s를 사용하여 SQL 인젝션 공격을 방지하는 안전한 쿼리입니다.
                cursor.execute(sql, (uid, pw)) #입력받은 값 쿼리에 대입하여 실행
                row = cursor.fetchone() # 실행한 한줄 가져오기

                if row: # 일치하는 회원있거나 결과가 None이아니면
                    member = Member.from_db(row) # 딕셔너리를 Member객체로 변환
                    # 2. 계정 활성화 여부 체크
                    if not member.active: # active = 0일경우 실행
                        print("비활성화된 계정입니다. 관리자에게 문의하세요.")
                        return

                    Session.login(member) #세션에 로그인한 회원 객체 저장
                    print(f"{member.name}님 로그인 성공 ({member.role})")
                else: # 결과가없거나, 두가지 입력 정보가 다를경우
                    print("아이디 또는 비밀번호가 틀렸습니다.")
        except Exception as e:  # 오류 발생 시 원인 파악을 위해 Exception 추가 추천
            print(f"MemberService.login() 메서드 오류 발생: {e}")
        finally:
            conn.close()

        # 1. %s 파라미터화: sql 변수에 직접 변수를 넣지 않고 %s를 쓰는 이유는
        #    보안(SQL Injection 방지) 때문입니다. DB가 값을 안전하게 처리하도록 맡기는 방식입니다.
        # 2. Member.from_db(row): DB에서 가져온 로우 데이터를 우리가 만든
        #    'Member 객체'로 바꾸는 핵심 단계입니다. 이제부터는 member.name 처럼 편하게 씁니다.
        # 3. active 체크: 아까 tinyint(1)로 설정했던 값을 여기서 검사하여,
        #    탈퇴했거나 정지된 회원이 로그인을 시도하는 것을 차단합니다.

    @classmethod
    def logout(cls):
        # 1. 먼저 세션에 로그인 정보가 있는지 확인
        if not Session.is_login():
            print("\n[알림] 현재 로그인 상태가 아닙니다.")
            return

        # 2. 세션의 로그인 정보 삭제
        Session.logout()
        print("\n[성공] 로그아웃 되었습니다. 안녕히 가세요!")

    @classmethod
    def signup(cls): # 객체 생성 없이 MemberService.signup()으로 호출
        print("\n[회원가입]")
        #회원가입 로직은 DB에 새로운 데이터를 안전하게 집어넣는 트랜잭션(Transaction) 처리가 핵심
        uid = input("아이디: ")

        conn = Session.get_connection() #DB연결 객체 생성
        try:
            with conn.cursor() as cursor: # DB 작업을 위한 커서 생성
                # 1. 중복 체크
                check_sql = "SELECT id FROM members WHERE uid = %s"
                cursor.execute(check_sql, (uid,)) # 데이터를 튜플 형태로 전달

                # SQL 쿼리 결과에서 단 한 개의 행(row)만 튜플(tuple) 형태로 반환합니다.
                # 호출할 때마다 다음 행으로 넘어가며, 더 이상 행이 없으면 None을 반환합니다.
                # 딕셔너리 커서 사용 시 딕셔너리 형태로도 출력됩니다
                # 튜플()소괄호 - 불변성, 읽기만가능, 수정기능없어서 빠름 , DB파라미터전달, 변하지않는값
                #"튜플은 데이터를 안전하게 보존하기 위한 '박제된 리스트'입니다.
                # 특히 DB에 값을 넘길 때 쉼표를 찍는 이유는, 파이썬에게 이게 그냥 글자가 아니라
                # '전달할 데이터 묶음'이라는 것을 명확히 알려주기 위함입니다!"

                # 1. SQL 인젝션 방지 (보안성)
                # 2. 데이터 무결성 (안정성)
                # 3. 메모리 효율 성능 가볍다

                if cursor.fetchone(): #조회 결과 있다면
                    print("이미 존재하는 아이디입니다.")
                    return # 가입중단 , 함수종료

                pw = input("비밀번호: ")
                name = input("이름: ")

                # 2. 데이터 삽입
                insert_sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
                cursor.execute(insert_sql, (uid, pw, name)) #DB에 데이터 삽입명령
                conn.commit() # 실제 DB에 최종 반영(확정)
                print("회원가입 완료! 로그인해 주세요.")

        except Exception as e:
            conn.rollback()
            # 트랜젝션 : with안쪽에 2개이상의 sql문이 둘다 true일때는 commit()
            #                    2중 한개라도 오류가 발생하면 rollback()
            print(f"회원가입 오류: {e}")

        finally:
            conn.close()

        # 1. (uid,): 파이썬에서 요소가 하나인 튜플을 만들 때는 반드시 뒤에 쉼표(,)를 찍어야 합니다.
        #    안 찍으면 그냥 괄호 친 문자열로 인식되어 SQL 실행 시 에러가 날 수 있습니다.
        # 2. auto_increment 활용: INSERT 문에서 id 컬럼을 명시하지 않았습니다.
        #    이렇게 하면 DB 설정에 따라 자동으로 1, 2, 3... 번호가 매겨집니다.
        # 3. 트랜잭션(Commit/Rollback):
        #    - Commit: "지금까지 한 작업이 완벽하니 실제 DB에 저장해!"라는 승인입니다.
        #    - Rollback: "중간에 에러 났으니까 지금까지 한 거 다 취소하고 없던 일로 해!"라는 명령입니다.

    @classmethod # 기존 데이터 변경 UPDATE로직, 메모리에 떠있는 Session정보까지 업데이트
    def modify(cls):  # 회원정보 수정 클래스메서드
        if not Session.is_login(): # 현재 로그인 상태 확인
            print("로그인 후 이용 가능합니다.")
            return

        member = Session.login_member # 세션에 저장된 '나'의 객체 가져옴
        print(f"내정보확인 : {member}")  # 현재 내정보 출력 Member.__str__()
        print("\n[내 정보 수정]\n1. 이름 변경  2. 비밀번호 변경 3. 계정비활성 및 탈퇴 0. 취소")
        sel = input("선택: ")

        new_name = member.name #변경 전 이름을 기본값으로 설정
        new_pw = member.password #변경 전 비밀번호 기본값으로 설정

        if sel == "1":
            new_name = input("새 이름: ") # 입력받아서 넣음
        elif sel == "2":
            new_pw = input("새 비밀번호: ")
        elif sel == "3":
            print("회원 중지 및 탈퇴를 진행합니다.")
            cls.delete() #같은 클래스 내의 delete메서드 호출
            return # 탈퇴 후 수정로직을 타지 않도록 종료
        else:
            return

        conn = Session.get_connection() # DB연결 시도
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE members SET name = %s, password = %s WHERE id = %s"
                # SQL 업데이트 문: 이름과 비번을 동시에 수정 (ID 기준)
                cursor.execute(sql, (new_name, new_pw, member.id))
                # 튜플로 데이터 전달: (새이름, 새비번, 기준ID) 순서 중요
                conn.commit() # DB에 최종 반영

                # 메모리(세션) 정보도 동기화
                member.name = new_name
                member.password = new_pw
                print("정보 수정 완료")

        except Exception as e:
            conn.rollback()  # 에러 발생 시 수정 취소
            print(f"수정 오류: {e}")
        finally:
            conn.close()  # DB 연결 해제


    @classmethod
    def delete(cls):
        if not Session.is_login(): #세션의 회원 객체 없으면 중단
            return
        member = Session.login_member #세션의회원객체를 member변수에 참조(연결)
        # 1. '대입'이 아니라 '참조':
        #    이 코드는 데이터를 새로 복사해오는 것이 아니라, 메모리에 떠 있는
        #    그 회원 객체를 같이 바라보는 것입니다. (리모컨을 하나 더 만드는 것과 같아요.)
        # 2. 편리함:
        #    매번 Session.login_member.name, Session.login_member.id 라고 쓰면
        #    코드가 길어지니까, member라는 짧은 별명을 붙여서 편하게 쓰려는 목적이 큽니다.

        print("\n[회원 탈퇴]\n1. 완전 탈퇴  2. 계정 비활성화")
        sel = input("선택: ")

        conn = Session.get_connection() # DB연결 객체 생성(DB 서버와 통신할 수 있는 '통로'를 염)
        try:
            with conn.cursor() as cursor: #SQL실행을 위한 커서 생성/ SQL 명령어를 실어 나를 '일꾼(객체)'을 만듦
                if sel == "1":
                    sql = "DELETE FROM members WHERE id = %s"
                    #완전탈퇴 DB에서 goekd god (row) 완전 삭제
                    cursor.execute(sql, (member.id,))# 튜플 형태 (쉼표 주의!)
                    # 커서가 있어야만 execute(실행) 명령을 내릴 수 있음
                    # 일꾼에게 SQL 문장을 전달함
                    print("회원 탈퇴 완료")
                elif sel == "2":
                    sql = "UPDATE members SET active = FALSE WHERE id = %s"
                    # active 만 0으로 변경
                    cursor.execute(sql, (member.id,))
                    print("계정 비활성화 완료")

                    # conn.cursor() as cursor
                    # 1. 왜 필수인가?:
                    #    conn 객체는 단순히 연결 상태만 유지합니다. 실제로 SQL을 문법에 맞게 검사하고,
                    #    DB에 던지고, 그 결과를 다시 받아오는 모든 "행동"은 cursor가 담당합니다.
                    #
                    # 2. with문의 역할:
                    #    `with`를 사용하면 SQL 작업이 끝나자마자 일꾼(cursor)이 사용했던 메모리를
                    #    즉시 반납합니다. (작업이 끝나면 트럭을 차고지에 넣는 것과 같습니다.)
                    #
                    # 3. 튜플 전달:
                    #    cursor.execute()가 튜플을 요구하는 것도 "트럭에 짐을 실을 때 정해진 상자(튜플)에
                    #    담아서 줘!"라고 일꾼과 약속되어 있기 때문입니다.

                conn.commit() #DB변경사항 최종 반영
                Session.logout() #탈퇴처리, 세션정보도 로그아웃

        except Exception as e:  # 오류 발생 시 실행
            conn.rollback()  # 작업 취소하고 이전 상태로 복구
            print(f"탈퇴 처리 오류: {e}")

        finally:  # 성공/실패 여부와 상관없이 무조건 실행
            conn.close()  # DB 연결 종료

    # 1. Hard Delete (완전 탈퇴): DELETE 문을 사용하여 데이터를 물리적으로 지웁니다.
    #    복구가 어렵지만 저장 공간을 아낄 수 있습니다.
    # 2. Soft Delete (비활성): 실제 데이터를 지우지 않고 active 컬럼값만 바꿉니다.
    #    나중에 복구가 가능하며 관리자가 활동 내역을 추적할 수 있어 실무에서 선호합니다.
    # 3. Session.logout(): 탈퇴하거나 비활성화된 회원은 더 이상 시스템을 이용할 수
    #    없어야 하므로, 메서드 마지막에 로그아웃 처리를 하여 메인 화면으로 돌려보냅니다.



























