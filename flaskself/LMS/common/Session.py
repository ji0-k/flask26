#세션에서 DB접속 관리
# HTML , CSS , JS : W3C (웹표준)
# 차후에는 이 페이지가 DB관리하는 connection 영역이 될 것
# 파이참에서 DB관리 메뉴 , 오른쪽 세개 쌓인 팬케잌

import pymysql
#파이썬으로 MySQL 조작도구 쓰겠다 선언
# pip install pymysql 터미널 설치
# pip install cryptography
# 최신 MySQL(8.0 이상)은 보안이 강력 데이터를 암호화/ 파이썬이 그 암호를 풀 수 있는 기능을 설치
# 없으면 Authentication plugin 'caching_sha2_password' cannot be loaded 같은 인증 에러

class Session :
    login_member = None
    # 나중에 로그인이 성공하면 그 자리에 사용자 정보(객체)를 집어넣으려고 자리를 만들어 둔 것
    # 현재는 가르키는 대상이 없는 상태
    # 근데 왜? DB접속이 가능해?


    @staticmethod
    # 정적메서드(@staticmethod):
    # Session이라는 설계도(클래스)에서 직접 메서드를 호출 사용 가능
    # DB 연결의 성격:
    # DB연결은 특정 로그인사용자(객체)에게 종속된 기능아님
    # 시스템이 사용하는 도구, 객체 생성 여부와 상관없이 그냥 돌수 있게 설계함
    def get_connection() :
        # 클래스를 복사(인스턴스화)하지 않고
        # Session.get_connection()으로 바로 쓰겠다는 선언
        # DB연결 코드
        print("get connection()메서드 호출 , DB연결 성공")

        return pymysql.connect( # MySQL DB접속 계정 정보 들고 찾아가는 코드
            host="localhost",   # DB가 설치된 주소
            user="mbc",         # 접속 계정 id
            password="1234",
            db='lms',           # 사용할 DB이름
            charset='utf8mb4',  # 이모지 한글 깨지지않게 문자설정
            cursorclass=pymysql.cursors.DictCursor
            #중요! 결과를 튜플()이아닌 {}dict 형태로 받아와서
            # row['title'] 처럼 이름으로 데이터 꺼낼 수 있게 해줌
        )

    # @staticmethod 클래스내부의 변수(login_member)를 건드리지않고
    # 단순히 DB연결처럼 기능만 수행할 때 주로 사용

    # @classmethod 클래스 변수(login_member)의
    # 값을 읽거나 수정해야 할 때 사용 하면 더 명확하고 편리


    @classmethod  # 클래스메서드: 객체를 만들지 않고 클래스 자체(cls)를 조작할 때 사용
    def login(cls, member):  # cls는 Session 클래스 자신을 의미, member(매개변수)는 로그인한 유저 정보
        cls.login_member = member  # None이었던 클래스 변수 login_member에 유저 정보를 저장함

    @classmethod
    def logout(cls):
        cls.login_member = None

    @classmethod #이 문구 덕분에 아래 cls는 Session클래스 그 자체가 됨
    def is_login(cls): # 자동으로 Session클래스를 cls자리에 전달
        return cls.login_member is not None
        # cls.login_member = Session.login_member
        # 내 Session안에 로그인한정보 있는지, 값이 있는지
        # 값이 있다면(NOt None) TRUE , 값이 없다면(None) False

    @classmethod
    def is_admin(cls):  # cls는 Session 클래스 본체
        return cls.is_login() and cls.login_member.get('role') == "admin"
        # 먼저 로그인 여부 확인 후, 딕셔너리의 'role' 키 값이 "admin"인지 비교
        # .get('role')을 쓰면 키가 없을 때 에러 대신 None을 줘서 더 안전해요!

    @classmethod
    def is_manager(cls):  # cls는 Session 클래스 본체
        return cls.is_login() and cls.login_member.get('role') == "manage"
        # 먼저 로그인 여부 확인 후, 딕셔너리의 'role' 키 값이 "manage"인지 비교
        # .get()을 쓰면 데이터가 비어있어도 에러 없이 None을 줘서 안전하게 비교 가능함

