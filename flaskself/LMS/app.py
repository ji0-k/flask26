# pip install flask
from flask import Flask, request, render_template, session, redirect, url_for
#               플라스크, 요청-응답,    프론트 연결  , 상태저장소, 주소전달 , 주소생성
from common.Session import Session
from LMS.domain.Board import Board
from datetime import date

# 1. app.py : app선언 , 비밀번호 설정 , 디버그 설정
# 2. 메인 라우터 main.html
# 3. 로그인/로그아웃 라우터 -> login html만들기 logout은 세션빼고 메인루프
# 4. 회원가입 라우터 -> join html 만들기
#

app = Flask(__name__)
app.secret_key = 'aaaaaa'
################################################################################################
@app.route('/') # 브라우저에서 http://127.0.0.1:5678/ 로 접속했을 때 실행됩니다.
def main():    # 이 함수 이름(index)이 url_for에서 사용됩니다.
    return render_template('main.html') # templates 폴더 안의 index.html을 보여줍니다.
#---------------------------------------------------------------------------------------------#
@app.route('/login', methods=['GET', 'POST']) #http://localhost:5000/login
def login():
    if request.method == 'GET':
        return render_template('login.html')

    uid = request.form.get('uid')
    upw = request.form.get('upw')

    conn = Session.get_connection()
    try :
        with conn.cursor() as cursor :
            sql = "select id, name, uid, role from members where uid = %s AND password = %s"
            cursor.execute(sql, (uid, upw))
            user = cursor.fetchone()

        if user : # 찾은계정잇으면 브라우저 세션에 보관
            today = date.today()  # 현재 날짜 (YYYY-MM-DD)
            with conn.cursor() as cursor:
                check_sql = "SELECT id FROM attendance WHERE user_id = %s AND log_date = %s"
                cursor.execute(check_sql, (user['id'], today))
                attendance_record = cursor.fetchone()

                if not attendance_record:
                    # 기록이 없다면 오늘 처음 로그인한 것이므로 attendance 테이블에 추가합니다.
                    # enter_time, last_pulse는 DB 설정에 따라 CURRENT_TIMESTAMP가 자동 입력됩니다.
                    insert_sql = """
                                 INSERT INTO attendance (user_id, log_date, study_minutes)
                                 VALUES (%s, %s, 0) \
                                 """
                    cursor.execute(insert_sql, (user['id'], today))
                    conn.commit()

            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_uid'] = user['uid']
            session['user_role'] = user['role']
            return redirect(url_for('main'))

        else :
            return  "<script>alert ('ID/PW'오류); history.back();</script>"

    finally :
        conn.close()
#---------------------------------------------------------------------------------------------#
@app.route('/logout') # 메서드=[] , 기본동작 get이라서 생략
def logout():
    session.clear()
    return redirect(url_for('main')) #로그아웃 후 로그인 페이지로 반환
#---------------------------------------------------------------------------------------------#
@app.route('/join', methods=['GET', 'POST'])
def join():
    # GET 요청 시 회원가입 1단계 페이지를 보여줍니다.
    if request.method == 'GET':
        return render_template('join.html')

    # POST 요청 시 사용자가 입력한 정보를 가져옵니다.
    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name')
    email = request.form.get('email', '')
    address = request.form.get('address', '')

    conn = Session.get_connection()  # 데이터베이스 연결
    try:
        with conn.cursor() as cursor:
            # 1. 아이디 중복 확인 절차
            cursor.execute("SELECT * FROM members WHERE uid = %s", (uid,))
            if cursor.fetchone():
                return "<script>alert('이미 사용 중인 아이디입니다.'); history.back();</script>"

            # 2. members 테이블에 기본 정보 저장
            sql = "INSERT INTO members (uid, password, name, email, address) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (uid, password, name, email, address))

            # 3. 중요: 방금 저장된 회원의 숫자 고유번호(PK)를 가져와 세션에 저장합니다.
            new_member_pk = conn.insert_id()
            conn.commit()  # DB에 영구 반영

            # 4. 세션 변수명을 'member_pk'로 정해서 2단계로 넘깁니다.
            session['member_pk'] = new_member_pk

            # 5. [수정] 이동할 함수 이름을 'join2'로 설정했습니다.
            return redirect(url_for('join2'))

    except Exception as e:
        print(f"회원가입 1단계 오류 : {e}")
        return "<script>alert('서버 오류 발생'); history.back();</script>"
    finally:
        conn.close()  # DB 연결 닫기


# ---------------------------------------------------------------------------------------------#

@app.route('/join2', methods=['GET', 'POST'])
def join2():
    m_id = session.get('member_pk')  # 1단계에서 넘겨준 숫자 ID
    if not m_id:
        return redirect(url_for('join'))

    if request.method == 'GET':
        return render_template('join2.html')

    # 사용자가 선택한 과목 이름들
    b_name = request.form.get('backend')
    s_name = request.form.get('server')
    d_name = request.form.get('db')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. members 테이블의 해당 회원 칸에 과목명 저장
            sql_m = """UPDATE members 
                       SET selected_backend=%s, selected_server=%s, selected_db=%s 
                       WHERE id=%s"""
            cursor.execute(sql_m, (b_name, s_name, d_name, m_id))

            # 2. scores 테이블에는 점수판만 생성 (기본값 0점)
            sql_s = "INSERT INTO scores (member_id) VALUES (%s)"
            cursor.execute(sql_s, (m_id,))

            conn.commit()

        session.pop('member_pk', None)
        return "<script>alert('가입 완료!'); location.href='/login';</script>"
    except Exception as e:
        print(f"저장 오류: {e}")
        return "<script>alert('오류가 발생했습니다.'); history.back();</script>"
    finally:
        conn.close()

# ---------------------------------------------------------------------------------------------#
@app.route('/member/edit', methods=['GET', 'POST'])
def member_edit():
    # 1. 로그인 체크 (세션 확인)
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'GET':
                # 기존 회원 정보 불러오기
                cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
                user_info = cursor.fetchone()
                return render_template('member_edit.html', user=user_info)

            # --- POST 요청: 정보 업데이트 ---
            # 폼에서 데이터 가져오기 (이메일, 주소는 비어있을 수 있으므로 기본값 '' 설정)
            new_name = request.form.get('name')
            new_pw = request.form.get('password')
            new_email = request.form.get('email', '')  # 값이 없으면 빈 문자열 저장
            new_address = request.form.get('address', '')  # 값이 없으면 빈 문자열 저장

            # 수강 과목 정보
            new_backend = request.form.get('backend')
            new_server = request.form.get('server')
            new_db = request.form.get('db')

            # 2. SQL 실행 (비밀번호 입력 여부에 따른 분기)
            if new_pw:
                # 비밀번호 변경 포함
                sql = """UPDATE members 
                         SET name=%s, password=%s, email=%s, address=%s, 
                             selected_backend=%s, selected_server=%s, selected_db=%s 
                         WHERE id=%s"""
                params = (new_name, new_pw, new_email, new_address,
                          new_backend, new_server, new_db, session['user_id'])
            else:
                # 비밀번호는 유지하고 나머지 정보만 변경
                sql = """UPDATE members 
                         SET name=%s, email=%s, address=%s, 
                             selected_backend=%s, selected_server=%s, selected_db=%s 
                         WHERE id=%s"""
                params = (new_name, new_email, new_address,
                          new_backend, new_server, new_db, session['user_id'])

            cursor.execute(sql, params)
            conn.commit()  # 변경사항 확정

            # 세션 정보 동기화
            session['user_name'] = new_name
            return "<script>alert('정보가 수정되었습니다.'); location.href='/mypage';</script>"

    except Exception as e:
        print(f"정보수정 에러 : {e}")
        return f"<script>alert('오류 발생: {e}'); history.back();</script>"
    finally:
        conn.close()  # DB 연결 종료
# ---------------------------------------------------------------------------------------------#
@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 회원 정보와 성적 정보를 JOIN하여 한꺼번에 가져옵니다.
            # members 테이블의 모든 정보 + scores 테이블의 평균(average), 등급(grade) 조회
            sql = """
                SELECT m.*, s.average, s.grade 
                FROM members m
                LEFT JOIN scores s ON m.id = s.member_id
                WHERE m.id = %s
            """
            cursor.execute(sql, (session['user_id'],))
            user_info = cursor.fetchone()

            # 2. 내가 쓴 게시글 개수 조회
            cursor.execute("SELECT COUNT(*) as board_count FROM boards WHERE member_id = %s", (session['user_id'],))
            board_count = cursor.fetchone()['board_count']

            # active가 TRUE인(활성화된) 게시글만 개수를 셉니다.
            sql_count = "SELECT COUNT(*) as cnt FROM boards WHERE member_id = %s AND active = TRUE"
            cursor.execute(sql_count, (session['user_id'],))
            board_count = cursor.fetchone()['cnt']

            # [추가] 댓글 수 (active인 것만)
            cursor.execute("SELECT COUNT(*) as cnt FROM comments WHERE member_id = %s AND active = TRUE",
                           (session['user_id'],))
            comment_count = cursor.fetchone()['cnt']

            # [추가 팁] 내가 받은 총 좋아요 수도 궁금하다면?
            sql_likes = "SELECT SUM(good_count) as total_likes FROM boards WHERE member_id = %s"
            cursor.execute(sql_likes, (session['user_id'],))
            total_likes = cursor.fetchone()['total_likes'] or 0  # 좋아요가 없으면 0

            return render_template('mypage.html', user=user_info, board_count=board_count, total_likes=total_likes)
    finally:
        conn.close()
# ---------------------------------------------------------------------------------------------#

# 1. 게시글 목록 보기
@app.route('/board')
def board_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 전체 게시글 개수 조회 (페이지네이션 계산용)
            cursor.execute("SELECT COUNT(*) as cnt FROM boards WHERE active = TRUE")
            total_count = cursor.fetchone()['cnt']
            total_pages = (total_count + per_page - 1) // per_page

            # 2. 통합 데이터 조회: boards의 모든 컬럼 + 작성자 이름 + 댓글 수
            sql = """
                SELECT b.*, 
                       m.name as writer_name, 
                       m.uid as writer_uid, 
                       (SELECT COUNT(*) FROM comments c 
                        WHERE c.board_id = b.id AND c.active = TRUE) as comment_count
                FROM boards b 
                JOIN members m ON b.member_id = m.id
                WHERE b.active = TRUE
                ORDER BY b.id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, (per_page, offset))
            rows = cursor.fetchall()

            # DB 행 데이터를 Board 객체 리스트로 변환
            boards = [Board.from_db(row) for row in rows]

            return render_template('board_list.html',
                                   boards=boards,
                                   page=page,
                                   total_pages=total_pages)
    finally:
        conn.close()


# 2. 게시글 상세 보기 및 조회수 증가
# 게시글 상세보기 (댓글 목록 포함)
@app.route('/board/view/<int:board_id>')
def board_view(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 조회수 증가
            cursor.execute("UPDATE boards SET view_count = view_count + 1 WHERE id = %s", (board_id,))

            # 2. 게시글 상세 정보 조회
            sql_board = """
                SELECT b.*, m.name as writer_name, m.uid as writer_uid
                FROM boards b 
                JOIN members m ON b.member_id = m.id
                WHERE b.id = %s AND b.active = TRUE
            """
            cursor.execute(sql_board, (board_id,))
            row = cursor.fetchone()
            if not row: return "<script>alert('게시글이 없습니다.'); history.back();</script>"
            board = Board.from_db(row)

            # 3. 댓글 목록 조회 (작성자 이름 포함)
            sql_comments = """
                SELECT c.*, m.name as writer_name 
                FROM comments c
                JOIN members m ON c.member_id = m.id
                WHERE c.board_id = %s AND c.active = TRUE
                ORDER BY c.id ASC
            """
            cursor.execute(sql_comments, (board_id,))
            comments = cursor.fetchall()  # 댓글 리스트(dict 형태)

            conn.commit()
            return render_template('board_view.html', board=board, comments=comments)
    finally:
        conn.close()


# 좋아요 기능
@app.route('/board/like/<int:board_id>')
def board_like(board_id):
    if 'user_id' not in session: return "<script>alert('로그인이 필요합니다.'); history.back();</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE boards SET good_count = good_count + 1 WHERE id = %s", (board_id,))
            conn.commit()
        return redirect(url_for('board_view', board_id=board_id))
    finally:
        conn.close()


# 댓글 작성 기능
@app.route('/comment/write', methods=['POST'])
def comment_write():
    if 'user_id' not in session: return "<script>alert('로그인 후 이용 가능합니다.'); history.back();</script>"

    board_id = request.form.get('board_id')
    content = request.form.get('content')
    member_id = session.get('user_id')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO comments (board_id, member_id, content) VALUES (%s, %s, %s)"
            cursor.execute(sql, (board_id, member_id, content))
            conn.commit()
        return redirect(url_for('board_view', board_id=board_id))
    finally:
        conn.close()


# 3. 게시글 삭제 (진짜 삭제 대신 active = FALSE 처리 추천)
@app.route('/board/delete/<int:board_id>')
def board_delete(board_id):
    if 'user_id' not in session:
        return '<script>alert("로그인 필요"); location.href="/login";</script>'

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # [수정] 본인 글인지 확인 후 active 필드만 FALSE로 변경 (데이터 보존)
            sql = "UPDATE boards SET active = FALSE WHERE id = %s AND member_id = %s"
            cursor.execute(sql, (board_id, session['user_id']))
            conn.commit()

            if cursor.rowcount > 0:
                return "<script>alert('삭제되었습니다.'); location.href='/board';</script>"
            else:
                return "<script>alert('삭제 권한이 없습니다.'); history.back();</script>"
    finally:
        conn.close()

# 댓글 삭제 기능
@app.route('/comment/delete/<int:comment_id>')
def comment_delete(comment_id):
    # 1. 로그인 체크
    if 'user_id' not in session:
        return "<script>alert('로그인이 필요합니다.'); location.href='/login';</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 2. 삭제하려는 댓글의 작성자와 게시글 ID 조회
            cursor.execute("SELECT member_id, board_id FROM comments WHERE id = %s", (comment_id,))
            comment = cursor.fetchone()

            if not comment:
                return "<script>alert('존재하지 않는 댓글입니다.'); history.back();</script>"

            # 3. 권한 체크 (작성자 본인 OR 매니저(4) OR 관리자(5))
            user_id = session.get('user_id')
            user_role = session.get('user_role', 1) # 세션에 role이 저장되어 있다고 가정

            if comment['member_id'] == user_id or user_role >= 4:
                # 권한이 있으면 삭제(비활성화) 처리
                cursor.execute("UPDATE comments SET active = FALSE WHERE id = %s", (comment_id,))
                conn.commit()
                return redirect(url_for('board_view', board_id=comment['board_id']))
            else:
                return "<script>alert('삭제 권한이 없습니다.'); history.back();</script>"
    finally:
        conn.close()
################################################################################################
# 3. 디버그 모드 실행 (코드를 수정하면 서버가 자동으로 재시작됨)
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5678)
    # host = '0.0.0.0' 누가요청하던 응답해라
    # port = 5000 플라스크에서 사용하는 포트번호
    # debug = true 콘솔에서 디버그를 보겠다.
    # 수정된 코드 즉각 바로 수정 출력