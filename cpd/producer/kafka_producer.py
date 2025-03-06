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

    # 예시: 5개의 채널(streamer id)을 리스트로 정의
    channel_list = [
        '17aa057a8248b53affe30512a91481f5',
        '0dad8baf12a436f722faa8e5001c5011',
        '6e06f5e1907f17eff543abd06cb62891',
        'cd04c50c6ff488ac96f8900e26e5b993',
    ]

    with open('/app/cookies.json') as f:
        cookies = json.load(f)

    logger = get_logger()
    broker = "kafka:9092"

    threads = []

    for channel in channel_list:
        chat_instance = ChzzkChat(channel, cookies, logger, broker)
        t = threading.Thread(target=chat_instance.run, name=f"ChatThread-{channel}")
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
