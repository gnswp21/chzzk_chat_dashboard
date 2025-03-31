FROM python:3.9

WORKDIR /app
RUN pip install requests
COPY fetch_live_info.py /app/fetch_live_info.py
COPY sort_channels.py /app/sort_channels.py
RUN mkdir  /app/temp

# CMD ["sh", "-c", "python fetch_live_info.py && python sort_channels.py"]