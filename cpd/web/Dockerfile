FROM python:3.9-slim

WORKDIR /app

COPY web.py /app/web.py

RUN pip install pandas streamlit pymysql pymongo cryptography streamlit-autorefresh


EXPOSE 8501

CMD ["streamlit", "run", "web.py"]