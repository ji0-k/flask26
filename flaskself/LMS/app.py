# pip install flask
from flask import Flask, request, render_template, session, redirect, url_for, send_from_directory
#               플라스크, 요청-응답,    프론트 연결  , 상태저장소, 주소전달 , 주소생성
from common.Session import Session
from LMS.domain.Board import Board
from LMS.domain.Score import Score
from datetime import date , datetime
from LMS.service.PostService import PostService
import os


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

   # --- 이메일 처리 부분 수정 ---
    email_id = request.form.get('email_id', '')  # HTML의 name="email_id" 값 가져오기
    email_domain = request.form.get('email_domain', '')  # HTML의 name="email_domain" 값 가져오기

    # 두 값을 합쳐서 하나의 이메일 주소로 만듭니다.
    if email_id and email_domain:
        email = f"{email_id}@{email_domain}"
    else:
        email = ""  # 값이 없으면 빈 문자열 혹은 None 처리

    # --- 주소 처리 부분도 수정 (상세주소 포함) ---
    address = request.form.get('address', '')
    address_detail = request.form.get('address_detail', '')
    address = f"{address} {address_detail}".strip()
    # ---------------------------------------

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
            # 1. 회원 정보와 성적 정보를 JOIN하여 한꺼번에 조회
            sql = """
                SELECT m.*, s.average, s.grade 
                FROM members m
                LEFT JOIN scores s ON m.id = s.member_id
                WHERE m.id = %s
            """
            cursor.execute(sql, (session['user_id'],))
            user_info = cursor.fetchone()

            # 2. 활성화된(active = TRUE) 게시글 개수 조회
            sql_count = "SELECT COUNT(*) as cnt FROM boards WHERE member_id = %s AND active = TRUE"
            cursor.execute(sql_count, (session['user_id'],))
            board_count = cursor.fetchone()['cnt']

            # 3. 댓글 수 조회 (활성화된 것만)
            # 제공해주신 DB 이미지의 member_id와 active 컬럼을 사용합니다.
            cursor.execute("SELECT COUNT(*) as cnt FROM comments WHERE member_id = %s AND active = TRUE",
                           (session['user_id'],))
            comment_count = cursor.fetchone()['cnt']

            # 4. 내가 쓴 게시글이 받은 총 좋아요 수 합계
            sql_likes = "SELECT SUM(good_count) as total_likes FROM boards WHERE member_id = %s"
            cursor.execute(sql_likes, (session['user_id'],))
            total_likes = cursor.fetchone()['total_likes'] or 0

            # [수정 포인트] render_template의 인자에 comment_count를 추가했습니다.
            return render_template('mypage.html',
                                   user=user_info,
                                   board_count=board_count,
                                   comment_count=comment_count,  # 이 부분이 추가되었습니다.
                                   total_likes=total_likes)
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
    if not session.get('user_id'):
        return '''
                <script>
                    alert("로그인 후 이용해주세요.");
                    location.href = "/login";
                </script>
            '''
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
@app.route('/board/write',methods=['GET','POST']) #http://localhost:5000/board/write
def board_write():
    #1. 사용자가 '글쓰기' 버튼을 눌러서 들어왔을 때 (화면보여주기)
    if request.method == 'GET':
        # 로그인 유무
        if 'user_id' not in session:
            return '<script>alert("로그인후 이용가능"); location.href="/login";</script>'
        return render_template('board_write.html') #프론트 안만들어서 template에 만들기
            # redirect와 url은 셋트 , get으로 호출해서 보여줄때
            # render_template은 html. 으로 객체 보낼때 사용

    #2. 사용자가 '등록하기' 버튼을 눌러서 데이터를 보냈을 때 (DB저장)
    elif request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        #세션에 저장된 고르인 유저의id (member_id)
        member_id = session.get('user_id')
        conn = Session.get_connection()
        try :
            with conn.cursor() as cursor:
                sql = "INSERT INTO boards(member_id,title,content) VALUES(%s,%s,%s)"
                cursor.execute(sql, (member_id, title, content))
                conn.commit()
            return  redirect(url_for('board_list')) #저장 후 게시글 목록으로 이동 #http://localgo
                # redirect와 url은 셋트 , get으로 호출해서 보여줄때
                # render_template은 html. 으로 객체 보낼때 사용
        except Exception as e :
            print(f"글 작성 에러 : {e}")
            return "저장 중 에러 발생"
        finally:
            conn.close()


@app.route('/board/edit/<int:board_id>', methods=['GET', 'POST'])
def board_edit(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 화면 보여주기(기존데이터 로드)
            if request.method == 'GET':
                sql = "SELECT * FROM boards WHERE id = %s"
                cursor.execute(sql, (board_id,))
                row = cursor.fetchone()

                if not row :
                    return "<script>alert('존재하지 않는 게시글입니다.'); history.back();</script>"

                # 본인 확인 로직
                if row['member_id'] != session.get('user_id'):
                    return "<script>alert('수정 권한이 없습니다.'); history.back();</script>"
                print(row)
                board = Board.from_db(row)
                return render_template('board_edit.html', board=board)

            # 2. 실제 Db업데이트 처리
            elif request.method == 'POST':
                title = request.form.get('title')
                content = request.form.get('content')

                sql = "UPDATE boards SET title = %s, content = %s WHERE id = %s"
                cursor.execute(sql, (title, content, board_id))
                conn.commit()

                return redirect(url_for('board_view', board_id=board_id))
    finally:
        conn.close()

# ---------------------------------------------------------------------------------------------#
# 파일처리용 게시판의 특징
# 1. 파일 업로드 / 다운로드가 가능
# 2. 단일 파일 / 다중파일 업로드 처리
# 3. 서비스 패키지를 활용
## 4. /UPLOAD 라는 폴더 사용 / 용량 제한 16MB
# 5. 파일명 중복 방지용 코드 활용
# 6. 부모객체 삭제시 자식객체 삭제 되게 CASCADE 처리

UPLOAD_FOLDER = 'uploads/'
#폴더가 없으면 자동생성
if not os.path.exists(UPLOAD_FOLDER): # import os 상단에 추가
    os.makedirs(UPLOAD_FOLDER)

# config 환경설정
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#최대 업로드 용량 제한 (예 16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# bit -> 0, 1
# 1byte -> 8bit -> 0~255까지 256개의 값을 가지고 있다
# 1kB -> 1024byte
# 1MB -> 1024kbyte
# 1GB -> 1024Mbyte
# 1TB -> 1024Gbyte
# 1PB -> 1024Tbyte
# 1XB -> 1024Pbyte

@app.route('/filesboard/write', methods=['GET', 'POST'])
def filesboard_write():
    # 세션에 사용자 정보가 없으면 로그인 페이지로 리다이렉트
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')  # 폼에서 제목 가져오기
        content = request.form.get('content')  # 폼에서 내용 가져오기

        # 핵심: getlist를 사용해야 여러 개의 파일을 리스트 형태로 한 번에 가져올 수 있습니다.
        files = request.files.getlist('files')
        #파일처리시 html에 필수 코드 : enctype="multipart/form-data">

        # 서비스 레이어를 호출하여 게시글과 파일을 저장
        if PostService.save_post(session['user_id'], title, content, files):
            return "<script>alert('게시글이 등록되었습니다.'); location.href='/filesboard';</script>"
        else:
            return "<script>alert('등록 실패'); history.back();</script>"

    # GET 요청 시 글쓰기 페이지 렌더링
    return render_template('filesboard_write.html')


# 파일 게시판 목록
@app.route('/filesboard')
def filesboard_list():
    posts = PostService.get_posts()
    return render_template('filesboard_list.html', posts=posts)


# 파일 게시판 상세 보기
@app.route('/filesboard/view/<int:post_id>')
def filesboard_view(post_id):
    post, files = PostService.get_post_detail(post_id) # 반환 2개이니까 받을 때도 2개로 받아야함
    if not post:
        return "<script>alert('해당 게시글이 없습니다.'); location.href='/filesboard';</script>"
    return render_template('filesboard_view.html', post=post, files=files)
                #                                                  여기서 리턴도 두개로 반환해야함
# send_from_directory 사용하여 자료 다운로드 가능
@app.route('/download/<path:filename>')
def download_file(filename):
    # 파일이 저장된 폴더(uploads)에서 파일을 찾아 전송합니다.
    # 프론트 <a href="{{ url_for('download_file', filename=file.save_name) }}" ...> 이부분 처리용
    # filename은 서버에 저장된 save_name입니다.
    # 브라우저가 다운로드할 때 보여줄 원본 이름을 쿼리 스트링으로 받거나 DB에서 가져와야 합니다.

    origin_name = request.args.get('origin_name') # 주소를 통해 넘어오는것
    return send_from_directory('uploads/', filename, as_attachment=True, download_name=origin_name)
    # from flask import send_from_directory (필수플라스크 내장 메서드)
    #   return send_from_directory('uploads/', filename)는 브라우져에서 바로 열어버림
    #   as_attachment=True 로 하면 파일 다운로드 창을 띄움
    #   저장할 파일명은 download_name=origin_name 로 지정


@app.route('/filesboard/delete/<int:post_id>') # 게시글로
def filesboard_delete(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 삭제 전 작성자 확인을 위해 정보 조회
    post, _ = PostService.get_post_detail(post_id)
    # _은 리턴값을 사용하지 않겠다 라는 관례적인 표현 (_) 사용하지 않는 변수
    # 두개 리턴되었으니까

    if not post:
        return "<script>alert('이미 삭제된 게시글입니다.'); location.href='/filesboard';</script>"

    # 본인 확인 (또는 관리자 권한)
    if post['member_id'] != session['user_id'] and session.get('user_role') != 'admin':
        return "<script>alert('삭제 권한이 없습니다.'); history.back();</script>"

    if PostService.delete_post(post_id):
        return "<script>alert('성공적으로 삭제되었습니다.'); location.href='/filesboard';</script>"
    else:
        return "<script>alert('삭제 중 오류가 발생했습니다.'); history.back();</script>"

# 다중파일 수정용
@app.route('/filesboard/edit/<int:post_id>', methods=['GET', 'POST'])
def filesboard_edit(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        files = request.files.getlist('files')  # 다중 파일 가져오기

        if PostService.update_post(post_id, title, content, files):
            return f"<script>alert('수정되었습니다.'); location.href='/filesboard/view/{post_id}';</script>"
        return "<script>alert('수정 실패'); history.back();</script>"

    # GET 요청 시 기존 데이터 로드
    post, files = PostService.get_post_detail(post_id)
    if post['member_id'] != session['user_id']:
        return "<script>alert('권한이 없습니다.'); history.back();</script>"

    return render_template('filesboard_edit.html', post=post, files=files)




# ---------------------------------------------------------------------------------------------#
@app.route('/studyroom')
def studyroom():
    # 1. 로그인 체크
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 2. 현재 사용자의 선택 과목 정보 가져오기
            sql = "SELECT selected_backend, selected_server, selected_db FROM members WHERE id = %s"
            cursor.execute(sql, (session['user_id'],))
            user_courses = cursor.fetchone()

            # 3. 과목별 강의 영상 데이터 (연습용 유튜브 링크)
            video_links = {
                'Java': 'https://www.youtube.com/embed/DNCBaeCoMug',
                'Python': 'https://www.youtube.com/embed/T6z-0dpXPvU',
                'Node.js': 'https://www.youtube.com/embed/Tt_tKhhhJqY',
                'AWS': 'https://www.youtube.com/embed/LU8x1UEcPFA',
                'Docker': 'https://www.youtube.com/embed/p1-wm-ThnTI',
                'MySQL': 'https://www.youtube.com/embed/DoGlXWqKqBE',
                'Oracle': 'https://www.youtube.com/embed/79cfNIPu0e4'
            }

            # 사용자가 선택한 과목들에 해당하는 링크만 필터링해서 리스트로 생성
            my_lectures = []
            for category in ['selected_backend', 'selected_server', 'selected_db']:
                course_name = user_courses[category]
                if course_name: # 과목이 선택되어 있다면
                    my_lectures.append({
                        'category': category.replace('selected_', '').upper(), # 카테고리 이름 정리
                        'name': course_name,
                        'url': video_links.get(course_name, '') # 딕셔너리에서 링크 추출
                    })

            return render_template('studyroom.html', lectures=my_lectures)
    finally:
        conn.close()

# ---------------------------------------------------------------------------------------------#
@app.route('/attendance')
def attendance_view():
    if 'user_id' not in session:
        return '<script>alert("로그인 후 이용 가능합니다."); location.href="/login";</script>'

    user_id = session['user_id']
    today = datetime.now().strftime('%Y-%m-%d')
    conn = Session.get_connection()

    try:
        with conn.cursor() as cursor:
            # 1. 오늘 기록이 있는지 확인 (없으면 입실 처리)
            sql_check = "SELECT * FROM attendance WHERE user_id = %s AND log_date = %s"
            cursor.execute(sql_check, (user_id, today))
            attendance_data = cursor.fetchone()

            if not attendance_data:
                # 첫 방문 시 입실(Insert)
                sql_insert = "INSERT INTO attendance (user_id, log_date) VALUES (%s, %s)"
                cursor.execute(sql_insert, (user_id, today))
                conn.commit()
                # 새로 생성된 데이터를 다시 가져옴
                cursor.execute(sql_check, (user_id, today))
                attendance_data = cursor.fetchone()
            else:
                # 이미 기록이 있다면 체류 시간 업데이트 (현재 시간 - 마지막 신호 시간)
                # 5분 이상 머물렀는지 판별하기 위해 last_pulse를 갱신
                sql_update = """
                    UPDATE attendance 
                    SET study_minutes = TIMESTAMPDIFF(MINUTE, enter_time, CURRENT_TIMESTAMP)
                    WHERE user_id = %s AND log_date = %s
                """
                cursor.execute(sql_update, (user_id, today))
                conn.commit()

            # 2. 나의 최근 출결 리스트 가져오기 (최근 10일)
            sql_list = "SELECT * FROM attendance WHERE user_id = %s ORDER BY log_date DESC LIMIT 10"
            cursor.execute(sql_list, (user_id,))
            attendance_list = cursor.fetchall()

            return render_template('attendance.html',
                                   today_data=attendance_data,
                                   attendance_list=attendance_list)
    finally:
        conn.close()

########################################[ 성적 메뉴 ]###################################################
#주의사항 : role에 admin과 manager만 cud를 제공한다 / USER에게는 자신의 성적  R 만 제공
@app.route('/score/add') # http://localhost:5000/score/add?uid=test1&name=test1
def add_score():
    user_role = session.get('user_role', 1)  # 기본값 1(USER)
    if user_role < 4:
        return "<script>alert('권한 없음'); history.back();</script>"

    target_uid = request.args.get('uid')
    target_name = request.args.get('name')
    # args.get : 주소를(URL) 통해 데이터가 넘어가는 값 주소뒤에 ?k=v&k=v ~~~

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 대상 학생의 id 찾기
            cursor.execute("SELECT id FROM members WHERE uid = %s",(target_uid,))
            student = cursor.fetchone()

            # 2. 기존의 성적이 있는지 조회
            existing_score = None

            if student :
                cursor.execute("SELECT * FROM scores WHERE member_id = %s",(student['id'],))
                row = cursor.fetchone()
                print(row) # 테스트용 코드로 dict타입으로 콘솔 출력
                if row :
                    existing_score = Score.from_db(row)
                    # 기존에 만든 Score.from_db활용
                    # 위쪽 객체 로드 처리 : from LMS.domain import Board, Score

            return render_template('score_form.html',
            # html에 자료 전송하는코드
                                   target_uid = target_uid,
                                   target_name = target_name,
                                   score = existing_score) # 객체전달

    except Exception as e:
        return {f"{e}": "데이터 조회 중 오류가 발생했습니다."}

    finally:
        conn.close()


@app.route('/score/save',methods=['POST'])
def score_save():
    if session.get('user_role', 1) < 4:
        return "권한오류", 403
        #웹페이지 오류페이지로 교체

    # 폼 데이터 수집: 새로운 과목명 반영
    target_uid = request.form.get('target_uid')
    db_score = int(request.form.get('db', 0))  # db 필드명 반영
    server_score = int(request.form.get('server', 0))  # server 필드명 반영
    backend_score = int(request.form.get('backend', 0))  # backend 필드명 반영

    conn = Session.get_connection()

    try:
        with conn.cursor() as cursor:
            # 1. 대상학생의 id(pk) 가져오기 -> 학생의 고유 번호 가져오기
            cursor.execute("SELECT id FROM members WHERE uid = %s",(target_uid,))
            student = cursor.fetchone()
            print(student) #학번 출력

            if not student :
                return "<script>alert('존재하지 않는 학생입니다.')</script>"

            #2. Score 객체 생성 (계산 프로퍼티 활용)
            temp_score = Score(member_id=student['id'], db=db_score, server=server_score, backend=backend_score)
            #            __init__ 를 활용하여 객체 생성

            #3. 기존 데이터가 있는지 확인
            cursor.execute("SELECT id FROM scores WHERE member_id = %s",(student['id'],))
            is_exist = cursor.fetchone()

            if is_exist: # 성적이 있으면 id 나오고 , 없으면 None처리
                # UPDATE실행
                sql = """
                        UPDATE scores 
                        SET db = %s, server = %s, backend = %s 
                        WHERE member_id = %s
                """
                cursor.execute(sql, (temp_score.db, temp_score.server, temp_score.backend, student['id']))

            else :
                # INSERT 실행
                sql = """
                        INSERT INTO scores(member_id, db, server, backend)
                        VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (student['id'], temp_score.db, temp_score.server, temp_score.backend))

            conn.commit()
            return f"<script>alert('{target_uid} 학생 성적 저장 완료'); location.href= '/score/list';</script>"

    # except Exception as e:
    #     return {f"{e}": "데이터 조회 중 오류가 발생했습니다."}

    finally:
        conn.close()

@app.route('/score/list') # http://localhost:5000/score/list -> get
def score_list():
    # 1. 권한 체크 (관리자나 매니저만 볼 수 있게 설정)
    if session.get('user_role', 1) < 4:
        return "<script>alert('권한이 없습니다.'); history.back();</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 2. JOIN을 사용하여 학생 이름(name)과 성적 데이터를 함께 조회
            # 성적이 없는 학생은 제외하고, 성적이 있는 학생들만 총점 순으로 정렬
            sql = """
                SELECT m.name, m.uid, s.* FROM scores s
                JOIN members m ON s.member_id = m.id
                ORDER BY s.total DESC
            """

            cursor.execute(sql)
            datas = cursor.fetchall()
            # print(f"sql결과 : {datas}")


            # 3. DB에서 가져온 딕셔너리 리스트를 Score 객체 리스트로 변환
            score_objects = [] #객체로 넣으려고 리스트 만들었다
            for data in datas:
                # Score 클래스에 정의하신 from_db 활용
                s = Score.from_db(data)  # dict타입 Score객체로 만들어서 s라고 하기 [직렬화]
                # 객체에 없는 이름(name) 정보는 수동으로 살짝 넣어주기, join에서 만든 값 사용
                s.name = data['name']
                s.uid = data['uid']
                score_objects.append(s)
            return render_template('score_list.html', scores=score_objects) #프론트에서 써먹으려고 위에서 객체로 만들어 객체로 보냄
            #                                       프론트 화면 ui에, 성적담긴 객체 리스트 전달함

    except Exception as e:
        return {f"{e}": "성적리스트 조회 중 오류가 발생했습니다."}

    finally:
        conn.close()

@app.route('/score/members') # http://localhost:5000/score/members -> get
def score_members():
    if session.get('user_role', 1) < 4:
        return "<script>alert('권한이 없습니다.'); history.back();</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT m.id, m.uid, m.name, s.id AS score_id
                FROM members m
                LEFT JOIN scores s ON m.id = s.member_id
                WHERE m.role <= 5
                ORDER BY m.name ASC
            """

            cursor.execute(sql)
            members = cursor.fetchall()
            return render_template('score_member_list.html', members=members)
    finally:
        conn.close()

@app.route('/score/my') # http://localhost:5000/score/my -> get
def score_my():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 내 ID로만 조회
            sql = "SELECT * FROM scores WHERE member_id = %s"
            cursor.execute(sql, (session['user_id'],))
            row = cursor.fetchone()

            # Score 객체로 변환 (from_db 활용)
            score = Score.from_db(row) if row else None

            return render_template('score_my.html', score=score)
    finally:
        conn.close()
########################################[ 성적 메뉴 종료 ]#################################################

########################################[ 교 구 몰 ]#################################################

@app.route('/shop/items')
def shop_list():
    """상품 전체 목록 보기"""
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # DB의 items 테이블에서 모든 상품 정보를 가져옵니다.
            sql = "SELECT id, code, name, category, price, stock FROM items ORDER BY id DESC"
            cursor.execute(sql)
            items = cursor.fetchall()
        return render_template('shop_items.html', items=items)
    except Exception as e:
        print(f"상품 목록 조회 오류: {e}")
        return "상품을 불러오는 중 오류가 발생했습니다."
    finally:
        conn.close()


@app.route('/shop/add_cart', methods=['POST'])
def shop_add_cart():
    """장바구니에 담기 (세션 활용)"""
    if 'user_id' not in session:
        return "<script>alert('로그인이 필요합니다.'); location.href='/login';</script>"

    item_id = request.form.get('item_id')
    qty = int(request.form.get('qty', 1))

    # 장바구니는 DB가 아닌 세션에 리스트 형태로 임시 저장합니다.
    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']
    # 이미 담긴 상품인지 확인 후 수량만 조절하거나 새로 추가
    for item in cart:
        if item['id'] == item_id:
            item['qty'] += qty
            break
    else:
        cart.append({'id': item_id, 'qty': qty})

    session['cart'] = cart  # 변경된 장바구니 세션 업데이트
    session.modified = True

    return "<script>alert('장바구니에 담겼습니다.'); location.href='/shop/items';</script>"


@app.route('/shop/cart')
def shop_cart():
    """장바구니 보기"""
    if 'user_id' not in session:
        return "<script>alert('로그인이 필요합니다.'); location.href='/login';</script>"

    cart_items = session.get('cart', [])  # 세션에서 장바구니 리스트 가져오기
    display_cart = []  # 화면에 뿌려줄 상세 데이터 리스트
    total_payment = 0  # 총 결제 금액

    if cart_items:
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                for cart in cart_items:
                    # 기존 items 테이블 컬럼명 그대로 사용
                    sql = "SELECT id, name, price FROM items WHERE id = %s"
                    cursor.execute(sql, (cart['id'],))
                    item = cursor.fetchone()

                    if item:
                        item_total = item['price'] * cart['qty']  # 품목별 합계
                        total_payment += item_total
                        # 상세 정보 합치기
                        display_cart.append({
                            'id': item['id'],
                            'name': item['name'],
                            'price': item['price'],
                            'qty': cart['qty'],
                            'subtotal': item_total
                        })
        finally:
            conn.close()

    return render_template('shop_cart.html', cart=display_cart, total_payment=total_payment)


@app.route('/shop/cart/delete/<int:item_id>')
def shop_cart_delete(item_id):
    """장바구니에서 특정 상품 삭제"""
    if 'cart' in session:
        # 세션의 cart 리스트에서 id가 일치하지 않는 것들만 남깁니다 (필터링)
        # item['id']가 문자열일 수 있으므로 str()로 변환하여 비교합니다.
        session['cart'] = [item for item in session['cart'] if str(item['id']) != str(item_id)]
        session.modified = True  # 세션 변경 사항 강제 반영

    return redirect(url_for('shop_cart'))

@app.route('/shop/cart/clear')
def shop_cart_clear():
    """장바구니 전체 비우기"""
    session.pop('cart', None) # 세션에서 cart 항목 자체를 제거
    return redirect(url_for('shop_cart'))


@app.route('/shop/checkout', methods=['POST'])
def shop_checkout():
    if 'user_id' not in session:
        return "<script>alert('로그인이 필요합니다.'); location.href='/login';</script>"

    cart_items = session.get('cart', [])
    if not cart_items:
        return "<script>alert('장바구니가 비어있습니다.'); location.href='/shop/items';</script>"

    # --- 주문서 폼에서 보낸 데이터 가져오기 ---
    order_email = request.form.get('order_email')  # 사용자가 확인/수정한 이메일
    order_phone = request.form.get('order_phone')  # 새로 입력한 핸드폰 번호
    order_address = request.form.get('order_address')  # 확인/수정한 배송 주소
    # ---------------------------------------

    member_id = session['user_id']
    total_payment = 0

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 총 결제 금액 계산 및 재고 확인
            processed_items = []
            for cart in cart_items:
                # items 테이블의 price와 stock을 가져옵니다.
                cursor.execute("SELECT id, price, stock FROM items WHERE id = %s", (cart['id'],))
                item = cursor.fetchone()

                if item:
                    # 재고 부족 체크
                    if item['stock'] < cart['qty']:
                        return f"<script>alert('재고가 부족합니다.'); history.back();</script>"

                    item_total = item['price'] * cart['qty']
                    total_payment += item_total
                    processed_items.append({
                        'id': item['id'],
                        'qty': cart['qty'],
                        'price': item['price']
                    })

            # 2. orders 테이블에 주문 메인 레코드 생성
            # 만약 DB에 phone, address 컬럼을 추가했다면 아래 SQL에 포함시키면 됩니다.
            sql_order = "INSERT INTO orders (member_id, total_price, status) VALUES (%s, %s, 'PAID')"
            cursor.execute(sql_order, (member_id, total_payment))
            order_id = conn.insert_id()

            # 3. order_items 상세 내역 저장 및 items 재고 차감
            for item in processed_items:
                # 상세 내역 저장
                sql_item = "INSERT INTO order_items (order_id, item_id, qty, price) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql_item, (order_id, item['id'], item['qty'], item['price']))

                # 재고 차감
                sql_update_stock = "UPDATE items SET stock = stock - %s WHERE id = %s"
                cursor.execute(sql_update_stock, (item['qty'], item['id']))

            conn.commit()
            session.pop('cart', None)  # 주문 완료 후 장바구니 비우기

            return redirect(url_for('shop_order_success', order_id=order_id))

    except Exception as e:
        if conn: conn.rollback()
        print(f"주문 최종 처리 오류 : {e}")
        return "<script>alert('서버 오류로 주문에 실패했습니다.'); history.back();</script>"
    finally:
        if conn: conn.close()


@app.route('/shop/order_form')
def shop_order_form():
    """주문 정보 입력 페이지 (이메일, 주소, 연락처 확인)"""
    if 'user_id' not in session:
        return "<script>alert('로그인이 필요합니다.'); location.href='/login';</script>"

    # 1. 장바구니 비어있는지 확인
    if not session.get('cart'):
        return "<script>alert('장바구니가 비어있습니다.'); location.href='/shop/items';</script>"

    # 2. 기존 회원 정보 불러오기 (이메일, 주소 등)
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # members 테이블에서 기존 가입 정보를 가져옵니다.
            sql = "SELECT email, address, name FROM members WHERE id = %s"
            cursor.execute(sql, (session['user_id'],))
            user_info = cursor.fetchone()

            # 장바구니 합계 금액 계산 (화면 표시용)
            total_payment = 0
            for cart in session['cart']:
                cursor.execute("SELECT price FROM items WHERE id = %s", (cart['id'],))
                item = cursor.fetchone()
                if item:
                    total_payment += item['price'] * cart['qty']

        return render_template('shop_order_form.html', user=user_info, total_payment=total_payment)
    finally:
        conn.close()


@app.route('/shop/order_success/<int:order_id>')
def shop_order_success(order_id):
    """주문 완료 페이지"""
    return render_template('shop_success.html', order_id=order_id)

@app.route('/myorder')
def my_order_list():
    """로그인한 사용자의 주문 내역 보기"""
    if 'user_id' not in session:
        return "<script>alert('로그인이 필요합니다.'); location.href='/login';</script>"

    member_id = session['user_id']
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 사용자의 주문 마스터 정보 가져오기 (orders 테이블)
            sql = """
                SELECT id, total_price, status, created_at 
                FROM orders 
                WHERE member_id = %s 
                ORDER BY created_at DESC
            """
            cursor.execute(sql, (member_id,))
            orders = cursor.fetchall()

            # 2. 각 주문별 상세 상품 정보 가져오기 (주문이 여러 개일 수 있으므로 반복)
            for order in orders:
                # order_items와 items 테이블을 조인하여 상품명을 가져옵니다
                item_sql = """
                    SELECT i.name, oi.qty, oi.price 
                    FROM order_items oi
                    JOIN items i ON oi.item_id = i.id
                    WHERE oi.order_id = %s
                """
                cursor.execute(item_sql, (order['id'],))
                order['order_details'] = cursor.fetchall() # order 딕셔너리에 items 리스트 추가

        return render_template('myorder.html', orders=orders)
    finally:
        conn.close()


# --- [관리자: 상품 등록] ---
@app.route('/shop/admin/items', methods=['GET', 'POST'])
def admin_item_add():
    if session.get('user_role', 0) < 4:
        return "<script>alert('권한이 없습니다.'); location.href='/';</script>"

    if request.method == 'POST':
        # items 테이블 컬럼명 그대로 사용
        code = request.form.get('code')
        name = request.form.get('name')
        category = request.form.get('category')
        price = request.form.get('price')
        stock = request.form.get('stock')

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO items (code, name, category, price, stock) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (code, name, category, price, stock))
                conn.commit()
            return "<script>alert('상품이 등록되었습니다.'); location.href='/shop/items';</script>"
        except Exception as e:
            print(f"상품 등록 오류: {e}")
            return "<script>alert('등록 실패'); history.back();</script>"
        finally:
            conn.close()

    return render_template('admin_item_add.html')




# --- [관리자: 주문 판매 현황] ---
@app.route('/shop/sales')
def shop_sales():
    if session.get('user_role', 0) < 3:
        return "<script>alert('권한이 없습니다.'); location.href='/';</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # orders와 members 테이블을 조인하여 누가 주문했는지 가져옵니다
            sql = """
                  SELECT o.id, m.name as member_name, o.total_price, o.status, o.created_at
                  FROM orders o
                           JOIN members m ON o.member_id = m.id
                  ORDER BY o.created_at DESC \
                  """
            cursor.execute(sql)
            sales = cursor.fetchall()
        return render_template('shop_sales.html', sales=sales)
    finally:
        conn.close()


@app.route('/shop/admin/items_edit')
def admin_item_edit_list():
    if session.get('user_role', 0) < 4:
        return "<script>alert('권한이 없습니다.'); location.href='/';</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 수정을 위해 모든 상품 목록을 불러옴
            cursor.execute("SELECT * FROM items ORDER BY id DESC")
            items = cursor.fetchall()
        return render_template('admin_item_list.html', items=items)
    finally:
        conn.close()


# 3. 실제 수정 실행 페이지 (위 리스트에서 '수정' 클릭 시 호출)
@app.route('/shop/admin/item_modify/<int:item_id>', methods=['GET', 'POST'])
def admin_item_modify(item_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'POST':
                # 수정된 값 반영
                code = request.form.get('code')
                name = request.form.get('name')
                category = request.form.get('category')
                price = request.form.get('price')
                stock = request.form.get('stock')

                sql = "UPDATE items SET code=%s, name=%s, category=%s, price=%s, stock=%s WHERE id=%s"
                cursor.execute(sql, (code, name, category, price, stock, item_id))
                conn.commit()
                return "<script>alert('수정 완료'); location.href='/shop/admin/items_edit';</script>"

            # 기존 데이터 불러오기
            cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
            item = cursor.fetchone()
            return render_template('admin_item_modify.html', item=item)
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