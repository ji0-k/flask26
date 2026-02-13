# pip install flask
from flask import Flask, request, render_template, session, redirect, url_for
#               플라스크, 요청-응답,    프론트 연결  , 상태저장소, 주소전달 , 주소생성
from common.Session import Session
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
    if request.method == 'GET':
        return  render_template('join.html') #회원가입페이지

    # 폼데이터가져오기
    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name')
    email = request.form.get('email', '')
    address = request.form.get('address','')

    conn = Session.get_connection()
    try :
        with conn.cursor() as cursor :
            cursor.execute("select * from members where uid = %s", (uid,)) #id중복체크
            if cursor.fetchone() :
                return f"<script>alert('ID 중복');window.location.href = '{url_for('login')}';</script>"

            sql = "INSERT INTO members (uid, password, name, email, address) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (uid, password, name, email, address))

            # 방금 INSERT된 데이터의 id(Auto Increment 값) 가져오기
            new_user_id = conn.insert_id()
            conn.commit()

            # 2단계에서 쓰기 위해 세션에 임시 저장
            session['temp_user_id'] = new_user_id

            # 바로 로그인 페이지가 아닌 강의 선택 페이지로 이동
            return redirect(url_for('join_step2'))

    except Exception as e:
        print(f"회원가입 오류 : {e}")
        return "<script>alert('서버 오류 발생'); history.back();</script>"

    finally: conn.close()
# 비밀번호를 암호화(hash)하여 저장하는 법 추가예정
#---------------------------------------------------------------------------------------------#
@app.route('/join/step2', methods=['GET', 'POST'])
def join_step2():
    # 1단계를 거치지 않고 바로 들어온 경우 차단
    if 'temp_user_id' not in session:
        return redirect(url_for('join'))

    conn = Session.get_connection()
    try:
        if request.method == 'GET':
            # 강의 목록을 DB에서 가져옵니다 (courses 테이블이 있다고 가정)
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name FROM courses")
                course_list = cursor.fetchall()
            return render_template('join_step2.html', courses=course_list)

        # POST 요청: 사용자가 선택한 강의들을 저장
        selected_courses = request.form.getlist('course_ids') # 체크박스 값들(리스트)
        user_id = session.get('temp_user_id')

        with conn.cursor() as cursor:
            for c_id in selected_courses:
                # 학생별 수강 강의 저장 (중간 테이블: member_courses)
                sql = "INSERT INTO member_courses (user_id, course_id) VALUES (%s, %s)"
                cursor.execute(sql, (user_id, c_id))
            conn.commit()

        # 가입 절차 완료 후 임시 세션 제거
        session.pop('temp_user_id', None)
        return "<script>alert('회원가입 및 수강 신청 완료!'); location.href='/login';</script>"

    except Exception as e:
        print(f"회원가입 2단계 오류 : {e}")
        return "<script>alert('강의 등록 중 오류 발생'); history.back();</script>"
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