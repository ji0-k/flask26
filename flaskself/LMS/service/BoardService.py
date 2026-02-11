from LMS.common.Session import Session
from LMS.domain.Board import Board

class BoardService:
    @classmethod
    def run(cls):
        if not Session.is_login():
            print("로그인 후 이용가능")
            return

        while True:
            conn = Session.get_connection()
            print(f"\n====== MBC 게시판 ({Session.login_member.name}접속중.) ======")
            cls.list_board(conn)
            print("1. 글 쓰기")
            print("2. 글 상세 보기 (수정/삭제 가능)")
            print("0. 뒤로가기")

            sel = input(">>> ")
            if sel == "1":
                cls.write_board()
            elif sel == "2":
                cls.view_detail()

            elif sel == "0":
                break


    @classmethod
    def list_board(cls, conn):  # 컨트롤러에서 전달받은 conn을 사용하도록 인자 추가
        print("\n" + "=" * 70)
        print(f"{'번호':<5} | {'제목':<25} | {'작성자':<10} | {'조회수':<5} | {'작성일'}")
        print("-" * 70)
        #게시판 목록을 가져와서 Board 객체 리스트로 반환하는 메서드
        try:
            with conn.cursor() as cursor:
                # JOIN 시 DB의 m.name을 객체의 writer_name으로 매칭하기 위해 별칭(AS) 사용
                sql = """
                      SELECT b.*, m.name AS writer_name, m.uid AS writer_uid
                      FROM boards b
                               JOIN members m ON b.member_id = m.id
                      ORDER BY b.id DESC \
                      """
                cursor.execute(sql)
                datas = cursor.fetchall()

                board_list = []  # 객체들을 담을 리스트

                for data in datas:
                    # 1. DB 데이터를 Board 객체로 변환 (객체화)
                    board_obj = Board.from_db(data)

                    # 2. 날짜 형식 처리 (출력용)
                    date_str = board_obj.created_at.strftime('%Y-%m-%d')

                    # 3. Board 클래스에서 만든 __str__ 메서드 활용하여 출력
                    # (객체의 속성인 writer_name이 자동으로 출력 로직에 녹아듭니다.)
                    print(f"{board_obj} | {date_str}")

                    # 4. 리스트에 추가 (Flask에서 사용하기 위함)
                    board_list.append(board_obj)

                return board_list  # 완성된 객체 바구니 반환

        except Exception as e:
            print(f"데이터 조회 중 오류 발생: {e}")
            return []

        # conn.close()는 이 함수를 호출한 app.py(컨트롤러)에서 처리하는 것이 일반적입니다.
        print("=" * 60)