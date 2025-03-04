import streamlit as st
import pandas as pd
import pymysql
import pymysql.cursors
from streamlit_autorefresh import st_autorefresh
import logging

# MySQL 연결 설정 (Docker Compose 환경의 경우 host가 "mysql"인 경우)
DB_CONFIG = {
    "host": "mysql",
    "port": 3306,
    "user": "root",
    "password": "example",
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

# 두 개의 탭으로 레이아웃 구성: 실시간 집계와 메시지 검색
tabs = st.tabs(["실시간 집계", "메시지 검색"])

# ----- 실시간 집계 탭 -----
with tabs[0]:
    st.header("실시간 메시지 집계 (10초 단위)")
    # 10초마다 탭 내 내용만 새로고침 (페이지 전체가 새로고침되지 않음)
    st_autorefresh(interval=10000, key="datarefresh")

    def get_aggregated_data():
        """
        Spark Streaming 작업에서 10초 윈도우로 집계한 결과가 저장된
        chat_messages_agg 테이블에서 집계 데이터를 읽어옵니다.
        """
        conn = pymysql.connect(**DB_CONFIG)
        query = """
            SELECT window_start as timestamp, sum(message_count) as count
            FROM chat_messages_agg
            GROUP BY timestamp
            ORDER BY timestamp DESC
            LIMIT 5
        """
        cursor = conn.cursor()
        # chat_messages 테이블에서 chat 컬럼에 키워드가 포함된 메시지 검색
        cursor.execute(query)
        results = cursor.fetchall()
        if results:
            # 컬럼명을 명시적으로 지정
            df_results = pd.DataFrame(results, columns=['timestamp', 'count'])
            # timestamp 컬럼을 datetime으로 변환 후, HH:MM:SS 형식으로 변경
            df_results['timestamp'] = pd.to_datetime(df_results['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
            df_results['timestamp'] = df_results['timestamp'].dt.strftime('%H:%M:%S')
            import altair as alt
            # Altair 차트를 생성하면서 x축 레이블 각도를 0으로 설정해 수평으로 표시
            chart = alt.Chart(df_results).mark_line().encode(
                x=alt.X('timestamp:N', axis=alt.Axis(labelAngle=0, title='Time')),
                y=alt.Y('count:Q', axis=alt.Axis(title='Count'))
            )
            st.altair_chart(chart, use_container_width=True)
            
        else:
            st.write("검색 결과가 없습니다.")
        cursor.close()
        conn.close()

    get_aggregated_data()
    # if not df_agg.empty:
    #     df_agg['timestamp'] = pd.to_datetime(df_agg['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    #     # NaT가 포함된 행 제거
    #     df_agg = df_agg.dropna(subset=['timestamp'])
    # else:
    #     st.write("집계 데이터가 없습니다.")

# ----- 메시지 검색 탭 -----
with tabs[1]:
    st.header("메시지 검색")
    keyword = st.text_input("검색할 키워드 입력")
    if st.button("검색"):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # chat_messages 테이블에서 chat 컬럼에 키워드가 포함된 메시지 검색
                query = "SELECT * FROM chat_messages WHERE chat LIKE %s"
                like_pattern = "%" + keyword + "%"
                cursor.execute(query, (like_pattern,))
                results = cursor.fetchall()
                if results:
                    df_results = pd.DataFrame(results)
                    st.dataframe(df_results)
                else:
                    st.write("검색 결과가 없습니다.")
            except Exception as e:
                st.error(f"쿼리 실행 중 에러 발생: {e}")
            finally:
                cursor.close()
                conn.close()
