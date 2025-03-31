import json
import logging
import os
import asyncio
import random
from ChzzkChatAPI.chzzk_chat import AsyncChzzkChat  # AsyncChzzkChat 임포트

def get_logger():
    formatter = logging.Formatter('%(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    return logger

async def run_with_retries(channelId, cookies, logger, broker, max_retries=5):
    retry_count = 0
    backoff_base = 2

    while True:
        try:
            chat_instance = AsyncChzzkChat(channelId, cookies, logger, broker)
            await chat_instance.run()
            break  # 정상 종료 시 반복 중단
        except Exception as e:
            retry_count += 1
            if retry_count > max_retries:
                logger.error(f"[{channelId}] 재시도 초과로 중단: {e}")
                break
            wait_time = backoff_base ** retry_count + random.uniform(0, 1)
            logger.warning(f"[{channelId}] 오류 발생, {retry_count}회차 재시도 예정 (대기 {wait_time:.1f}초): {e}")
            await asyncio.sleep(wait_time)

async def main():
    # 채널 목록 로드
    with open('/app/channel_list.json', encoding='utf-8') as f:
        channel_list = json.load(f)
    channelId_list = [channel['channelId'] for channel in channel_list][:100]  # 이 파드에서 담당할 채널 수

    # 쿠키 로드
    with open('/app/cookies.json') as f:
        cookies = json.load(f)

    logger = get_logger()
    broker = os.environ.get('BROKERS', 'kafka:9092')

    # 각 채널에 대해 run_with_retries 코루틴 생성
    tasks = [
        asyncio.create_task(
            run_with_retries(channelId, cookies, logger, broker)
        )
        for channelId in channelId_list
    ]

    # 모든 태스크 병렬 실행
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
