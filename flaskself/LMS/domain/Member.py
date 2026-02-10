# oop 기반의 Member 객체용
# DB에서 가져온 member데이터를 회원이라는 객체로 만들어 관리하겠다는 뜻
# 오타방지 , 데이터 보호 (클래스 내부에 숨김)
# DB에서 꺼내온 회원 데이터 담는 전용 그릇!

class Member:

    def __init__(self, id, uid, password , name, role="user",active=True):
        self.id = id
        # DB의 AUTO_INCREMENT로 생성된 번호를 담는 변수, 고유식별번호
        self.uid = uid
        self.password = password
        self.name = name
        self.role = role
        #사용자의 권한 저장, 기본값 "user"
        self.active = active
        #계정 활성상태 , DB의 tinyint(1)에 맞춰 기본값 1(활성)
        # [등급제(role) 설계 가이드] : 나중에 참고
        # 0: 비활성 (또는 별도의 active 필드 사용)
        # 1: 일반 회원
        # 2: 우수 회원
        # 3: 특별 회원
        # 4: 매니저
        # 5: 관리자

        # [실무에서 숫자를 쓰는 이유]
        # 1. 성능(Index): 문자열보다 숫자를 빨리 찾음
        #    회원이 100만 명일 때 '관리자'라는 글자를 찾는 것보다 숫자 5를 찾는 게 훨씬 빠릅니다.
        # 2. 정렬(Sorting): 등급순으로 회원을 나열할 때 '가나다'순이 아니라
        #    숫자 크기순으로 정렬하면 되니 코드가 매우 깔끔해집니다.
        # 3. 변경 용이성: "우수 회원"이라는 명칭이 "VIP 회원"으로 바뀌어도
        #    DB 데이터(숫자 2)는 건드릴 필요 없이 화면에 보여주는 글자만 바꾸면 됩니다.

    @classmethod
    def from_db(cls, row: dict): #row:dict, 딕셔너리타입으로 들어오라
        if not row:
            return None #데이터 없으면 빈손None으로 돌아감

        # return cls(
        #     row['id'],
        #     row['uid'],       # 순서가 틀리면 데이터가 꼬일 위험이 있음
        #     row['password'],  # DB에 'uid' 키가 없으면 바로 에러 발생
        #     row['name'],
        #     row['role'],
        #     row['active']
        # )
        return cls(  # db에 있는 정보를 dict 타입으로 받아와 에 넣음
            id=row.get('id'),         # DB 레코드의 PK 값을 가져와 객체의 id에 할당, (키가 없어도 에러 대신 None 반환)
            uid=row.get('uid'),       # 딕셔너리의 'uid' 값을 꺼내 객체의 uid 속성에 저장
            password=row.get('password'), # DB의 password 필드 값을 객체의 password 변수로 연결
            name=row.get('name'),     # 'name' 키에 해당하는 실명을 객체 내부로 복사
            role=row.get('role'),     # DB 등급(숫자/문자)을 객체의 권한 속성으로 전달
            active=bool(row.get('active')) # 활성화 여부를 판단해 True/False 객체 상태로 변환
        )
        # [전체 동작 설명]
        # "DB에서 한 줄(row) 꺼내온 딕셔너리 주머니에서, 필요한 알맹이(Value)들을
        # 하나하나 집어서 Member라는 새로운 객체 그릇에 옮겨 담는 과정입니다."

        #"DB 딕셔너리의 각 항목(Key)을 Member 객체의 속성(Variable)으로
        # 매핑(Mapping)하여 새 객체를 생성합니다."

    def is_admin(self): # 이 함수는 Member 객체 전용입니다.
        return self.role == "admin" # '나(self)'라는 회원의 등급만 확인

    # [작동 범위 설명]
    # 1. 호출 대상: 반드시 Member 객체가 생성된 후에만 사용할 수 있습니다.
    #    예: mem = Member.from_db(row) -> mem.is_admin() (O)
    # 2. 독립성: 다른 파일(예: Main.py)에서 쓰더라도, 반드시 Member 객체를 통해서만 실행됩니다.
    #    객체 외부에서 그냥 is_admin()이라고 부르면 "그런 함수 없다"고 에러가 납니다.

    def __str__(self):  # member객체를 문자열로 출력할 때 사용(테스트용)
        return f"{self.name}({self.uid}:{self.password}) [{self.role} ]"
