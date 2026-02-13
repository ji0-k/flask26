# OOP 객체생성 없이
import os, uuid
from LMS.common.Session import Session

class PostService:

    # 파일 게시물 저장
    # PostService.save_post 내부에서 post_id를 먼저 생성한 후,
    # 그 ID를 이용해 attachments 테이블에 파일 정보를 넣는 순서로 동작하고 있습니다.
    @staticmethod
    def save_post(member_id, title, content, files=None, upload_folder='uploads/'):
        """게시글과 첨부파일을 동시에 저장 (트랜잭션 처리)"""
        conn = Session.get_connection()  # from LMS.common import Session
        try:
            with conn.cursor() as cursor:
                # 1. 게시글(posts) 먼저 저장
                sql_post = "INSERT INTO posts (member_id, title, content) VALUES (%s, %s, %s)"
                cursor.execute(sql_post, (member_id, title, content))

                # 방금 INSERT된 게시글의 ID(PK) 가져오기
                post_id = cursor.lastrowid # 신규게시글의 번호
                # 파일첨부테이블에 들어갈 내용

                # 3. 다중 파일 처리
                if files:
                    for file in files:
                        if file and file.filename != '':
                            origin_name = file.filename
                            ext = origin_name.rsplit('.', 1)[1].lower()
                            save_name = f"{uuid.uuid4().hex}.{ext}"  # 상단에 import uuid
                            file_path = os.path.join(upload_folder, save_name)  # 상단에 import os

                            file.save(file_path)  # 서버에 저장 uploads/

                            # attachments 테이블에 각각 저장
                            sql_file = """INSERT INTO attachments (post_id, origin_name, save_name, file_path)
                                          VALUES (%s, %s, %s, %s)"""
                            cursor.execute(sql_file, (post_id, origin_name, save_name, file_path))

                conn.commit()
                return True

        except Exception as e:
            print(f"Error saving post: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # 파일게시물 목록
    @staticmethod
    def get_posts(): # 파일 전체 목록
        """작성자 이름과 첨부파일 개수를 함께 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 서브쿼리를 사용하여 해당 게시글에 연결된 첨부파일 개수(file_count)를 가져옵니다.
                sql = """
                      SELECT p.*, m.name as writer_name,
                      (SELECT COUNT(*) FROM attachments WHERE post_id = p.id) as file_count
                      FROM posts p JOIN members m ON p.member_id = m.id
                      ORDER BY p.created_at DESC 
                      """
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            conn.close()

    # 파일게시물 자세히보기
    @staticmethod
    def get_post_detail(post_id):
        """게시글 상세 정보와 첨부파일 정보를 함께 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. 조회수 증가
                cursor.execute("UPDATE posts SET view_count = view_count + 1 WHERE id = %s", (post_id,))

                # 2. 게시글 정보 조회 (작성자 이름 포함)
                sql_post = """
                           SELECT p.*, m.name as writer_name
                           FROM posts p
                                    JOIN members m ON p.member_id = m.id
                           WHERE p.id = %s 
                           """
                cursor.execute(sql_post, (post_id,))
                post = cursor.fetchone()

                # 3. 첨부파일 정보 조회 첨부파일 가져와
                cursor.execute("SELECT * FROM attachments WHERE post_id = %s", (post_id,))
                files = cursor.fetchall() #첨부 목록이 나온다

                conn.commit()
                return post, files #반환할때 파일이랑 post 출력
                # post는 posts에 , file은 files 에 있는
                # 롤백 할 필요는 없다? -> 하면 조회수 증가 됨
                # python의 장점 -> return에 두개 이상 걸 수 있음

        finally:
            conn.close()

    @staticmethod
    def delete_post(post_id, upload_folder='uploads/'):
        """게시글 및 관련 실제 파일 삭제"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. 삭제 전 첨부파일 정보 조회 (파일 삭제를 위해)
                cursor.execute("SELECT save_name FROM attachments WHERE post_id = %s", (post_id,))
                files = cursor.fetchall()

                # 2. 서버에서 실제 파일 삭제
                for f in files:
                    file_path = os.path.join(upload_folder, f['save_name'])
                    if os.path.exists(file_path):
                        os.remove(file_path)

                # 3. 게시글 삭제 (DB 외래키 ON DELETE CASCADE 설정 덕분에 attachments도 자동 삭제됨)
                #    삭제시 cascade옵션을 걸지않으면 자식테이블 데이터 선 삭제 후 부모테이블 데이터 후 삭제
                sql = "DELETE FROM posts WHERE id = %s"
                cursor.execute(sql, (post_id,))

                conn.commit()
                return True

        except Exception as e:
            print(f"Delete Error: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    @staticmethod  # 다중파일 수정 처리(기존파일 지우고 업데이트)
    def update_post(post_id, title, content, files=None, upload_folder='uploads/'):
        """게시글 수정 및 다중 파일 교체"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. 기본 정보 수정
                cursor.execute("UPDATE posts SET title=%s, content=%s WHERE id=%s", (title, content, post_id))

                # 2. 새 파일들이 들어왔을 경우만 기존 파일 삭제 및 교체
                # (아무 파일도 선택 안 하면 기존 파일 유지)
                if files and any(f.filename != '' for f in files):
                    # A. 기존 물리적 파일 삭제를 위해 save_name 조회
                    cursor.execute("SELECT save_name FROM attachments WHERE post_id = %s", (post_id,))
                    old_files = cursor.fetchall()
                    for old in old_files:
                        old_path = os.path.join(upload_folder, old['save_name'])
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    # B. DB에서 기존 첨부파일 기록 삭제
                    cursor.execute("DELETE FROM attachments WHERE post_id = %s", (post_id,))

                    # C. 새로운 파일들 저장
                    for file in files:
                        if file and file.filename != '':
                            origin_name = file.filename
                            ext = origin_name.rsplit('.', 1)[1].lower()
                            save_name = f"{uuid.uuid4().hex}.{ext}"
                            file_path = os.path.join(upload_folder, save_name)
                            file.save(file_path)

                            cursor.execute("""
                                           INSERT INTO attachments (post_id, origin_name, save_name, file_path)
                                           VALUES (%s, %s, %s, %s)
                                           """, (post_id, origin_name, save_name, file_path))

                conn.commit()
                return True

        except Exception as e:
            print(f"Update Error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()












