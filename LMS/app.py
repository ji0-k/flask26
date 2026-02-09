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
            sql = "SELECT id,name,uid, role \
            FROM members WHERE uid = %s AND password = %s "
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
            # BOM 브라우저 메서드, 경고창 alret       페이지 뒤로 이동하기

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
@app.route('/member/edit', methods=['GET','POST'])
def member_edit() :
    if 'user_id' not in session: # 세션에 있는 내용이 비었으면(로그인안된상태이면)
        return redirect(url_for('login'))  #로그인 경로로 보내기

    # 세션 내용이 있으면 DB연결 시작
    conn = Session.get_connection()
    try :
        with conn.cursor() as cursor:
            if request.method == 'GET' :
                #기존정보 불러오기
                cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],)) #회원 고유번호
                user_info = cursor.fetchone() #DB에서 가져온 dict
                return render_template('member_edit.html', user =user_info)
                # 가장 중요한 포인트                        get요청시 페이지 , 객체전달용 코드
            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw : # 비밀번호입력시에만 변경
                sql = "UPDATE members SET name = %s, password = %s WHERE uid = %s "
                cursor.execute(sql, (new_pw, session['user_id'],))
            else : # 이름만 변경
                sql = "UPDATE members SET name = %s WHERE id = %s"
                cursor.execute(sql, (new_name, session['user_id'],))

            conn.commit()
            session['user_name'] = new_name
            return "<script>alert('정보수정완료'); location.href='/mypage';</script>"

    except Exception as e:  # 예외 발생시 실행문
        print(f"정보수정 에러 : {e}")
        print("/n member_edit() 메서드를 확인하세요")

    finally: conn.close() # DB연결 종료!

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
            board_count = cursor.fetchone() # 개수를 세어 fetchone()에 넣음 -> board_count이름으로 갯수를 가지고잇음

            return render_template('mypage.html', user =user_info, board_count=board_count)
            # 결과반환                                mypage.html 에게 user객체와 board_count객체를 담아 보냄
            # 프론트에서 사용하려면 {{user.?????}}, {{board_count}}
    finally: conn.close()

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