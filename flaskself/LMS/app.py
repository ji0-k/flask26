# pip install flask
# python 만든 DB연동 콘솔 프로그램을 웹으로 연결하는 프레임워크
# 프레임 워크 : 미리 만들어 놓은 틀 안에서 작업하는 공간
from flask import Flask

# app.py는 flask로 서버를 동작하기 위한 파일명 (기본파일)

# static, templates 폴더 필수 ( 프론트엔드 용 파일 모이는곳)
# static (정적자원) : 서버의 별도 가공없이 파일 그대로 브라우저 전달 /css 디자인, /js 브라우저동작, /img 로고 배경 ...
# templates(동적자원) : 서버(flask)가 데이터를 채워 넣어(렌더링) 새로운HTML생성 보냄, jinja엔진 ,

# app. py  : app이라 지정하고 flask웹 서버 한대를 만들어서 프로그램 전체를 돌리겠다
# 라우팅(Routing) 설정: @app.route('/') 처럼 사용자가 어떤 주소로 접속했을 때 어떤 함수를 실행할지 결정합니다.
# 설정 관리: app.config['SECRET_KEY'] 처럼 웹 서비스에 필요한 각종 설정값을 저장합니다.
# 애플리케이션 실행: app.run() 명령어를 통해 실제로 웹 브라우저에서 접속 가능한 상태로 서버를 띄웁니다.

# app = Flask(__name__)#
# # 1. 세션 사용을 위한 비밀키 설정 (보안용 랜덤 문자열)
# app.secret_key = 'your_secret_key_here'
# # # 2. 파일 업로드 경로 설정
# app.config['UPLOAD_FOLDER'] = 'static/uploads'#
# # 3. 디버그 모드 실행 (코드를 수정하면 서버가 자동으로 재시작됨)
# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

# 1. app.py , app선언 , 비밀번호 설정 , 디버그 설정
# 2. 로그인 라우터 만들기

app = Flask(__name__)
app.secret_key = 'aaaaaa'

# 3. 디버그 모드 실행 (코드를 수정하면 서버가 자동으로 재시작됨)
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5678)
    # host = '0.0.0.0' 누가요청하던 응답해라
    # port = 5000 플라스크에서 사용하는 포트번호
    # debug = true 콘솔에서 디버그를 보겠다.
    # 수정된 코드 즉각 바로 수정 출력