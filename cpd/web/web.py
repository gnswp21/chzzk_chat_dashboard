import streamlit as st
import pandas as pd
import pymysql
import pymysql.cursors
from streamlit_autorefresh import st_autorefresh
import pytz
import logging
import os


MYSQL_HOST = os.environ.get('MYSQL_HOST', 'mysql')
BROKERS = os.environ.get('BROKERS', 'kafka:9092')
# MySQL 연결 설정 (Docker Compose 환경의 경우 host가 "mysql"인 경우)
DB_CONFIG = {
    "host": MYSQL_HOST,
    "port": 3306,
    "user": "user",
    "password": "password",
    "database": "mydb",
    "cursorclass": pymysql.cursors.DictCursor
}


def get_connection():
    """MySQL 데이터베이스에 연결합니다."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        st.error(f"DB 연결 실패: {e}")
        return None


st.title("메시지 대시보드")

# 채널 ID 입력
channelName = st.text_input("채널 이름을 입력하세요")
if not channelName:
    st.warning("먼저 채널이름을 입력하세요.")
    st.stop()

# 탭 구성: 실시간 집계, 닉네임 검색, 메시지 검색
tabs = st.tabs(["실시간 집계", "닉네임 검색", "메시지 검색"])
kst = pytz.timezone('Asia/Seoul')
# ----- 실시간 집계 탭 -----
with tabs[0]:
    st.header("실시간 메시지 집계 (5분 단위)")

    def get_aggregated_data(channelName):
        import altair as alt
        """
        5분간 채팅수
        """
        conn = pymysql.connect(**DB_CONFIG)
        query = """
            WITH windows AS (
                SELECT 
                    DATE_SUB(
                        FROM_UNIXTIME(UNIX_TIMESTAMP(NOW()) - (UNIX_TIMESTAMP(NOW()) %% (5 * 60))),
                        INTERVAL (seq + 1) * 5 MINUTE
                    ) AS window_start
                FROM (
                    SELECT 0 AS seq UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
                ) AS seq_table
            )
            SELECT 
                w.window_start,               
                IFNULL(COUNT(m.id), 0) AS message_count
            FROM windows w
            LEFT JOIN chat_messages m 
                ON m.timestamp >= w.window_start
                AND m.timestamp < DATE_ADD(w.window_start, INTERVAL 5 MINUTE)
                AND m.channelName = %s
            GROUP BY w.window_start
            ORDER BY w.window_start DESC
        """
        cursor = conn.cursor()
        cursor.execute(query, (channelName,))
        results = cursor.fetchall()
        if results:
            # 컬럼명을 명시적으로 지정
            df_results = pd.DataFrame(
                results, columns=['window_start', 'message_count'])

            df_results['window_start'] = pd.to_datetime(
                df_results['window_start'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
            df_results['window_start'] = df_results['window_start'].dt.tz_localize(
                'UTC').dt.tz_convert(kst)
            df_results['window_start'] = df_results['window_start'].dt.strftime(
                '%H:%M')

            # Altair 차트를 생성하면서 x축 레이블 각도를 0으로 설정해 수평으로 표시
            chart = alt.Chart(df_results).mark_line().encode(
                x=alt.X('window_start:N', axis=alt.Axis(
                    labelAngle=0, title='Time')),
                y=alt.Y('message_count:Q', axis=alt.Axis(title='Count'))
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("검색 결과가 없습니다.")
        cursor.close()
        conn.close()

    get_aggregated_data(channelName)

# ----- 닉네임 검색 탭 -----
with tabs[1]:
    st.header("닉네임 검색")
    nickname_keyword = st.text_input("검색할 닉네임 입력", key="nick_input")
    if st.button("검색", key="nick_search_btn"):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # chat_messages 테이블에서 입력된 채널 ID에 따른 데이터를 조회합니다.
                query = """
                SELECT timestamp, nickname, msg, chat_type
                FROM chat_messages
                WHERE channelName = %s
                """
                params = [channelName]
                # 키워드가 입력된 경우 nickname 컬럼에 해당 키워드가 포함된 메시지 검색
                if nickname_keyword:
                    query += " AND nickname = %s"
                    params.append(nickname_keyword)
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()
                if results:
                    df_results = pd.DataFrame(results)
                    # UTC → KST 변환
                    df_results['timestamp'] = pd.to_datetime(
                        df_results['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                    df_results['timestamp'] = df_results['timestamp'].dt.tz_localize(
                        'UTC').dt.tz_convert(kst)
                    # KST 기준으로 HH:MM:SS 형식으로 변환
                    df_results['timestamp'] = df_results['timestamp'].dt.strftime(
                        '%H:%M:%S')

                    st.dataframe(df_results)
                else:
                    st.write("검색 결과가 없습니다.")
            except Exception as e:
                st.error(f"쿼리 실행 중 에러 발생: {e}")
            finally:
                cursor.close()
                conn.close()

# ----- 메시지 검색 탭 -----
with tabs[2]:
    st.header("메시지 검색")
    message_keyword = st.text_input("검색할 메세지 입력", key="msg_input")
    if st.button("검색", key="msg_search_btn"):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # chat_messages 테이블에서 입력된 채널 ID에 따른 데이터를 조회합니다.
                query = """
                SELECT timestamp, nickname, msg, chat_type
                FROM chat_messages
                WHERE channelName = %s
                """
                params = [channelName]
                # 키워드가 입력된 경우 msg 컬럼에 해당 키워드가 포함된 메시지 검색
                if message_keyword:
                    query += " AND msg LIKE %s"
                    like_pattern = "%" + message_keyword + "%"
                    params.append(like_pattern)
                    query += " ORDER BY timestamp DESC LIMIT 100"
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()
                if results:
                    df_results = pd.DataFrame(results)
                    df_results['timestamp'] = pd.to_datetime(
                        df_results['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                    df_results['timestamp'] = df_results['timestamp'].dt.tz_localize(
                        'UTC').dt.tz_convert(kst)
                    # KST 기준으로 HH:MM:SS 형식으로 변환
                    df_results['timestamp'] = df_results['timestamp'].dt.strftime(
                        '%H:%M:%S')
                    st.dataframe(df_results)
                else:
                    st.write("검색 결과가 없습니다.")
            except Exception as e:
                st.error(f"쿼리 실행 중 에러 발생: {e}")
            finally:
                cursor.close()
                conn.close()
