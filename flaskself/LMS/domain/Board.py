class Board :
    def __init__(self,id, title, content, member_id,
                 active = True, created_at = None,
                 writer_name = None, writer_uid = None,
                 view_count = 0, good_count = 0,
                 comments = None, comment_count=0): # 인자 유지

            #1. 게시글의 기본정보 (PK 및 제목 내용)
            self.id = id                    
            self.title = title
            self.content = content
            self.member_id = member_id      

            #2. 상태 및 메타 데이터 (활성화 여부, 생성일)
            self.created_at = created_at
            self.active= active      

            #3. 추가 데이터
            self.writer_name = writer_name  
            self.writer_uid = writer_uid    
            self.view_count = view_count
            self.good_count = good_count

            # 댓글 데이터
            self.comments = comments if comments is not None else []
            self.comment_count = comment_count # 추가

    @classmethod
    def from_db(cls, row: dict):
        if not row : return None 
        return cls(
            id = row.get('id'),  
            title = row.get('title'),
            content = row.get('content'),
            member_id = row.get('member_id'),
            active = bool(row.get('active')),
            created_at = row.get('created_at'),
            writer_name = row.get('writer_name'),
            writer_uid = row.get('writer_uid'),
            view_count = row.get('view_count', 0),
            good_count = row.get('good_count', 0),
            comments = row.get('comments'),
            # [추가] 쿼리에서 가져온 댓글 개수를 매핑합니다.
            comment_count = row.get('comment_count', 0) 
        )

    def __str__(self): 
        writer = self.writer_name if self.writer_name else f"ID:{self.member_id}"
        return f"{self.id:<4} | {self.title:<28} | {writer:<10}| {self.view_count:<7}"