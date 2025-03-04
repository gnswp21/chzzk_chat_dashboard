# import json
# import time
# from kafka import KafkaProducer
from ChzzkChatAPI import *
from ChzzkChatAPI.chzzk_chat import *
import argparse
import logging
import json



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


if __name__ == "__main__":
    # 설정
    parser = argparse.ArgumentParser()

    # with open('/app/cookies.json') as f:
    #     cookies = json.load(f)
    cookies = ''

    streamer_id = 'bb382c2c0cc9fa7c86ab3b037fb5799c'
    parser.add_argument('--streamer_id', type=str, default=streamer_id)
    args = parser.parse_args()

    logger = get_logger()
    chzzkchat = ChzzkChat(args.streamer_id, cookies, logger, BROKER='kafka:9092')
    chzzkchat.run()
    
    # # 연결
    # conn = get_conn(config)    
    
    # # 메시지 받기
    # msg = get_msg(config, conn)
    
    # # 카프카 브로커로 정송
    # send_msg_to_kafka(msg)
    
    
