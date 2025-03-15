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

    with open('/app/channel_list.json', encoding='utf-8') as f:
        channel_list = json.load(f)

    channelId_list = [channel['channelId'] for channel in channel_list]

    with open('/app/cookies.json') as f:
        cookies = json.load(f)

    logger = get_logger()
    broker = os.environ.get('BROKERS', 'kafka:9092')

    threads = []

    for channelId in channelId_list:
        chat_instance = ChzzkChat(channelId, cookies, logger, broker)
        t = threading.Thread(target=chat_instance.run,
                             name=f"ChatThread-{channelId}")
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
