# OOP 기반의 Board 객체:
#       단순히 DB에서 가져온 데이터를 나열하는 것이 아니라, 게시판이라는 '개념'을 하나의 독립된 객체로 정의하여 관리합니다.
# 데이터 전용 그릇 (DTO):
#        데이터베이스(DB)에서 꺼내온 복잡한 게시판 데이터를 안전하고 깔끔하게 담아 이동시키는 역할을 합니다.
# 데이터 보호 및 캡슐화:
#       클래스 내부에 데이터를 숨겨서 외부의 잘못된 수정으로부터 보호하고, 오타로 인한 프로그래밍 실수를 방지합니다.

class Board :

    def __init__(self,id, title, content, member_id,
                 active = True, created_at = None,
                 writer_name = None, writer_uid = None,
                 view_count = 0, good_count = 0, comments = None):

            #1. 게시글의 기본정보 (PK 및 제목 내용)
            self.id = id                    # 게시글 고유 식별번호 (PK)
            self.title = title
            self.content = content
            self.member_id = member_id      # 작성자 고유 번호 (FK)

            #2. 상태 및 메타 데이터 (활성화 여부, 생성일)
            self.created_at = created_at
            self.active= active      # 게시글 노출 여부

            #3. 추가 데이터
            # JOIN 쿼리를 통해 가져온 작성자의 이름과 아이디를 담기
            self.writer_name = writer_name  # member테이블 JOIN
            self.writer_uid = writer_uid    # member테이블 JOIN
            self.view_count = view_count
            self.good_count = good_count

            # 댓글 데이터: 리스트 형태 []로 관리하며, 데이터가 없으면 빈 리스트로 초기화합니다.
            self.comments = comments if comments is not None else []


    @classmethod
    def from_db(cls, row: dict):
        #[역직렬화 메서드]
        #DB에서 꺼낸 한 줄(딕셔너리)을 Board 객체라는 그릇으로 옮겨 담습니다.

        if not row : return None # DB 비어있으면 객체 만들지 않고 종료
        return cls(
            id = row.get('id'),  # 딕셔너리의 'id'값을 객체의 id에 전달
            title = row.get('title'),
            content = row.get('content'),
            member_id = row.get('member_id'),
            active = bool(row.get('active')),

            # JOIN 쿼리를 통해 조회된 작성자 정보 매핑
            created_at = row.get('created_at'),
            writer_name = row.get('writer_name'),
            writer_uid = row.get('writer_uid'),

            # 수치 데이터 (조회수, 좋아요) 매핑
            view_count = row.get('view_count',0),
            good_count = row.get('good_count',0),
            comments = row.get('comments')
        )

    def __str__(self): # print(board)로 테스트용
        writer = self.writer_name if self.writer_name else f"ID:{self.member_id}"
        #                           작성자의 이름이있으면
        # 작성자의 이름을 writer에 넣고                   없으면 작성자의 번호를 넣는다
        return f"{self.id:<4} | {self.title:<28} | {writer:<10}| {self.view_count:<7}"



