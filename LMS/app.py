# pip install flask
# 파이썬으로 만든 DB연동 콘솔 프로그램을 웹으로 연결하는 프레임 워크
#  프레임 워크 : 미리 만들어놓은 틀 안에서 작업하는 공간

#app.py는 플라스크로 서버를 동작하기 위한 파일명 (기본파일)

# static, templates 폴더 필수 (프론트용 파일 모이는 곳)
#  static : 정적 파일을 모아 놓은( HTML, CSS , JS ....)
#  templates : 동적 파일을 모아 놓은 ( CRUD화면, 레이아웃, index 등 ...)
from flask import Flask, render_template, request , redirect, url_for, session
#                플라스크,  프론트 연결,     요청,응답,  주소전달 , 주소생성 , 상태저장소
from common.session import Session
from LMS.domain import Board
import math
app = Flask(__name__)
app.secret_key = 'aaaaaaaaa'
# 세션을 사용하기 위해 보안키 설정 (아무 문자열이나 입력 )


@app.route('/login',methods=['GET', 'POST']) #http://localhost:5000/login 이라는 경로 만들어짐
    # method는 웹에 동작을 관여한다.
    # GET : url 주소로 데이터를 처리( 보안상 취약, 빠름)
    # POST : body영역 데이터 처리 ( 보안상 좋음 , 대용량에서 많이 사용함)
    # 대부분 처음 화면(HTML렌더)을 요청할 때는 GET 방식으로 처리
    # 화면에 있는 내용을 백엔드로 전달할 때는 POST 방식으로 처리
def login():
    if request.method == 'GET' : # 처음 접속하면 GET방식으로 화면 출력용
        return render_template('login.html')
        # GET방식으로 요청하면 login.html 화면이 나옴
    # login.html에서 action="/login" method="POST" 처리용 코드
    # login.html에서 넘어어온 폼 데이터는 uid/upw
    uid = request.form.get('uid') # 요청한 폼 내용을 가져옴
    upw = request.form.get('upw') # request . form get
    # print("/login 에서 넘어온 폼 데이터 출력 테스트")
    # print(uid,upw)

    conn = Session.get_connection() # 교사용 DB에 접속용 객체
    try : # 예외 발생 가능성 있음
        with conn.cursor() as cursor: # DB에 커서객체 사용
        # 1.회원 정보 조회
            sql = "SELECT id,name,uid, role FROM members WHERE uid = %s AND password = %s "
        #                  uid가 동일 & pw가 동일
        #   id, name, uid, role 가져온다.
            cursor.execute(sql, (uid, upw))  # 쿼리문 실행
            user = cursor.fetchone() # 쿼리 결과 1개를 가져와 user변수에 넣음 (dict type)

        if user: # 찾은 계정이 있으면 브라우저의 세션영역에 보관한다
            session['user_id'] = user['id'] # 계정 일련 번호(자동생성 회원번호)
            session['user_name'] = user['name'] # 계정이름
            session['user_uid'] = user['uid'] # 계정 로그인 명
            session['user_role'] = user['role'] # 계정 권한
            # 세션에 저장완료
            # 브라우저에서 F12번 누르고 애플리케이션 탭에서 쿠키 항목에 가면 Session객체가 보임
            # 이것을 삭제하면 로그아웃 처리 됨
            # 원래 service 탭에 들어가야함
            return redirect(url_for('index'))
            # 처리 후 이동하는 경로 http://localhost:/index로 감 (GET메서드 방식)

        else : # 찾은 계정이 없다
            return "<script>alert('ID / PW 오류'); history.back();</script>"
            # BOM 브라우저 메서드, 경고창 alert       페이지 뒤로 이동하기

    finally:
        conn.close() #DB연결 종료 꼭!

@app.route('/logout' ) #methods=['GET') 기본동작이 get이라서 생략가능, ''뒤에 써있어야함
def logout():
    session.clear() #세션비우기
    return redirect(url_for('login')) #http://localhost:5000/login (get메서드방식)
    #     다음경로알려줌 (로그인페이지로)

@app.route('/join', methods=['GET','POST'])  # 회원가입용 함수
def join(): #http://localhost:5000/ get(화면출력, 회원가입용 창) post(화면 폼 처리용, submit->action돌면)
    if request.method == 'GET':
        return render_template('join.html') #로그인 화면용 프론트로 보냄
    # POST 메서드인 경우 폼으로 데이터가 넘어올때 처리
    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name') # 여기까지가 폼에서 넘어온 값을 변수에 넣음

    conn = Session.get_connection()  #db에 연결
    try : # 예외발생 가능성이 있는 코드
        with conn.cursor() as cursor:  # DB에 커서객체 사용
            # 아이디 중복 확인
            cursor.execute("SELECT * FROM members WHERE uid = %s ",(uid,)) #튜플이라 뒤에 쉼표
            if cursor.fetchone():
                return "<script>alert('ID 중복'); history.back();</script>"

            #회원정보 저장(role, active는 기본값이 들어감)
            sql = "INSERT INTO members(uid,password,name) VALUES(%s,%s,%s)"
            cursor.execute(sql, (uid, password, name))
            conn.commit()
            return  "<script>alert('회원가입 완료'); location.href='/login';</script>"
                                                # 다음 원하는 경로로 보내면됨, OR main

    except Exception as e : # 예외 발생시 실행문
        print(f"회원가입 에러 : {e}")
        print("/n join() 메서드를 확인하세요")

    finally: # 항상 실행문 뒤에 종료
        conn.close()
# @ app.route url생성
# get 메서드 프론트 페이지 출력
# post 값입력 받아서
# 개체로 보내는거
# 브라우저의 session코드 , 시크릿 코드 넣어주기
@app.route('/member/edit', methods=['GET', 'POST'])
def member_edit():
    if 'user_id' not in session:  # 세션에 있는 내용이 비었으면(로그인안된상태이면)
        return redirect(url_for('login'))  # 로그인 경로로 보내기

    print(f"{session['user_id']} login_session")

    # 세션 내용이 있으면 DB연결 시작
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'GET':
                #print("get method call")
                # 기존정보 불러오기
                cursor.execute("SELECT * FROM members WHERE id = %s ", (session['user_id'],))
                #print("sql call")
                user_info = cursor.fetchone()  # DB에서 가져온 dict
                #print(f"user_info call {user_info}")
                return render_template('member_edit.html', user=user_info)
                #                         가장 중요한 포인트 get요청시 페이지 , 객체전달용 코드
                # POST 요청: 정보 업데이트
            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw:  # 비밀번호 입력 시에만 변경
                sql = "UPDATE members SET name = %s, password = %s WHERE id = %s"
                cursor.execute(sql, (new_name, new_pw, session['user_id']))
            else:  # 이름만 변경
                sql = "UPDATE members SET name = %s WHERE id = %s"
                cursor.execute(sql, (new_name, session['user_id']))

            conn.commit()
            session['user_name'] = new_name  # 세션 이름 정보도 갱신
            return "<script>alert('정보가 수정되었습니다.'); location.href='/mypage';</script>"

    except Exception as e: # 예외 발생시 실행문
        print(f"정보수정 에러 : {e}")
        return "member_edit() 메서드를 확인하세요"

    finally:
        conn.close()  # DB연결 종료!

@app.route('/mypage') # http://localhost:5000/mypage get요청시 처리됨
def mypage() :
    if 'user_id' not in session:
        return redirect(url_for('login'))  #http://localhost:5000/login 으로 보냄
    conn = Session.get_connection() #DB연결
    try :
        with conn.cursor() as cursor:
            # 1. 내 상세 정보 조회
            cursor.execute("SELECT * FROM members WHERE id = %s ",(session['user_id'],))
            # 로그인한 정보를 가지고 db에서 찾아옴
            user_info = cursor.fetchone() # 찾아온 1개의 값을 user_info에 넣었음 (dict)

            # 2. 내가 쓴 게시글 개수 조회(작성하신 boards 테이블 활용)
            cursor.execute("SELECT COUNT(*) as board_count FROM boards WHERE member_id = %s ",(session['user_id'],))
            #                                                   boards 테이블에 조건 member_id 값을 가지고 찾아옴
            board_count = cursor.fetchone()['board_count'] # 개수를 세어 fetchone()에 넣음 -> board_count이름으로 갯수를 가지고잇음

            return render_template('mypage.html', user =user_info, board_count=board_count)
            # 결과반환                                mypage.html 에게 user객체와 board_count객체를 담아 보냄
            # 프론트에서 사용하려면 {{user.?????}}, {{board_count}}
            # redirect와 url은 셋트 , get으로 호출해서 보여줄때
            # render_template은 html. 으로 객체 보낼때 사용
    finally:
        conn.close()

 ####################################회원 crud end##############################################################################

 ###################################게시판 CRUD####################################################################
# 1.게시글 보기
@app.route('/board') #http://localhost:5000/board # 기본적으로 get방식
def board_list():
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #작성자 이름을 함께 가져오기 위해 JOIN사용
            sql = """
            SELECT b.*,m.name as writer_name
            FROM boards b 
            JOIN members m ON b.member_id = m.id
            ORDER BY b.id DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            boards = [Board.from_db(row) for row in rows]
            return render_template('board_list.html',boards=boards)
            # redirect와 url은 셋트 , get으로 호출해서 보여줄때
            # render_template은 html. 으로 객체 보낼때 사용
    finally:
        conn.close()

# 2. 게시글 자세히보기 # http://localhost:5000/board/view/99 (게시글 번호)
@app.route('/board/view/<int:board_id>')
def board_view(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # JOIN을 통해 작성자 정보 (name, id)를 함께조회
            sql = """
                SELECT b.*,m.name as writer_name , m.uid as writer_uid
                FROM boards b 
                JOIN members m ON b.member_id = m.id
                WHERE b.id = %s
               """
            cursor.execute(sql, (board_id,))
            row = cursor.fetchone()
            print(row)

            if not row :
                return "<script>alert ('존재하지 않는 게시글');history.back()</script>"

            #Board 객체로 변환 (앞서작성한 Board.py의 from_db활용)
            board = Board.from_db(row)
            return render_template('board_view.html', board= board)
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

# 3. 게시물삭제  작성자본인게시물삭제 확인단계필요
@app.route('/board/delete/<int:board_id>')
def board_delete(board_id):
    # 로그인 여부 확인 (필요시)
    # if 'user_id' not in session:
    #     return '<script>alert("로그인 후 이용 가능합니다."); location.href="/login";</script>'

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 본인 확인 로직을 추가하고 싶다면 WHERE member_id = %s 를 추가하세요.
            sql = "DELETE FROM boards WHERE id = %s"  # 저장된 테이블명 boards 사용
            cursor.execute(sql, (board_id,))
            conn.commit()

            if cursor.rowcount > 0:
                print(f"게시글 {board_id}번 삭제 성공")
            else:
                return "<script>alert('삭제할 게시글이 없거나 권한이 없습니다.'); history.back();</script>"
        return redirect(url_for('board_list'))

    except Exception as e:
        print(f"삭제 에러: {e}")
        return "삭제 중 오류가 발생했습니다."

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






















@app.route('/') # url 생성용 코드 http://localhost:5000/
                #             or http://192.168.0.0~~~ :5000/
def index(): #html 코드 넣을 수 있음
    return render_template('main.html')
    # render_template 웹브라우저로 보낼 파일명
    # templates라는 폴더에서 main.html을 찾아 보냄



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    # host = '0.0.0.0' 누가요청하던 응답해라
    # port = 5000 플라스크에서 사용하는 포트번호
    # debug = true 콘솔에서 디버그를 보겠다.