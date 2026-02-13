from LMS.common.Session import Session

__all__ = ['Session']
# 패키지 import 뒤에 * 처리용

# 패키지 구조 (LMS 패키지)

# MVC(Model-View-Controller) 패턴
# domain (Model): 데이터의 형태를 정의 (Score, Member 객체 등).
# service (Controller/Logic): DB 연동 및 비즈니스 로직 처리.
# app.py (Router/Main): 사용자의 요청(URL)을 받아서 어떤 서비스를 실행할지 결정하고 화면을 보여줌.