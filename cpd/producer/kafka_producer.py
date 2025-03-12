import json
import time
import logging
from ChzzkChatAPI import *
from ChzzkChatAPI.chzzk_chat import *


def get_logger():

    formatter = logging.Formatter('%(message)s')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # file_handler = logging.FileHandler('chat.log', mode="w")
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

if __name__ == '__main__':
    import threading
    import json
    import os

    # 예시: 5개의 채널(streamer id)을 리스트로 정의
    with open('/app/channel_list.json') as f:
        channel_list = json.load(f)
    channel_list = channel_list.values()
    
    with open('/app/cookies.json') as f:
        cookies = json.load(f)
    
   

    logger = get_logger()
    broker = os.environ.get('BROKERS', 'kafka:9092')

    threads = []

    for channel in channel_list:
        chat_instance = ChzzkChat(channel, cookies, logger, broker)
        t = threading.Thread(target=chat_instance.run, name=f"ChatThread-{channel}")
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
