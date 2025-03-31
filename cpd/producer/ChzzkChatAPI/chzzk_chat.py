import argparse
import asyncio
import datetime
import json
import logging

from ChzzkChatAPI import api
from ChzzkChatAPI.cmd_type import CHZZK_CHAT_CMD
import websockets
from aiokafka import AIOKafkaProducer


class AsyncChzzkChat:
    def __init__(self, streamer, cookies, logger, broker=None):
        self.streamer = streamer
        self.cookies = cookies
        self.logger = logger

        # 초기 인증 정보 (동기 방식으로 가져옴)
        self.userIdHash = api.fetch_userIdHash(self.cookies)
        self.chatChannelId = api.fetch_chatChannelId(self.streamer, self.cookies)
        self.channelName = api.fetch_channelName(self.streamer)
        self.accessToken, self.extraToken = api.fetch_accessToken(self.chatChannelId, self.cookies)
        self.sid = None

        if not broker:
            broker = "my-cluster-kafka-brokers.kafka.svc.cluster.local:9092"
        self.broker = broker

        self.producer = None  # aiokafka producer (나중에 초기화)
        self.websocket = None  # 웹소켓 연결 객체

    async def start_producer(self):
        """비동기 KafkaProducer 시작"""
        self.producer = AIOKafkaProducer(bootstrap_servers=self.broker)
        await self.producer.start()

    async def stop_producer(self):
        """KafkaProducer 종료"""
        if self.producer:
            await self.producer.stop()

    async def send_kafka_msg(self, channelName, now, chat_type, nickname, msg):
        """Kafka로 메시지를 비동기로 전송합니다."""
        topic = 'chzzk'
        message = json.dumps({
            "channelName": channelName,
            "chat_type": chat_type,
            "nickname": nickname,
            "msg": msg
        }, ensure_ascii=False)
        try:
            await self.producer.send_and_wait(topic, message.encode('utf-8'))
            self.logger.info(f"Kafka 메시지 전송 성공: {message}")
        except Exception as e:
            self.logger.error(f"Kafka 메시지 전송 실패: {e}")

    async def connect(self):
        """
        웹소켓 연결을 설정하고 인증 및 최근 채팅 내역 요청을 수행합니다.
        토큰 갱신도 이 단계에서 수행합니다.
        """
        # 토큰 및 채널 정보 갱신 (동기 함수 호출)
        self.chatChannelId = api.fetch_chatChannelId(self.streamer, self.cookies)
        self.accessToken, self.extraToken = api.fetch_accessToken(self.chatChannelId, self.cookies)

        uri = 'wss://kr-ss1.chat.naver.com/chat'
        self.websocket = await websockets.connect(uri)
        self.logger.info(f'{self.channelName} 채팅창에 연결 중...')

        default_payload = {
            "ver": "2",
            "svcid": "game",
            "cid": self.chatChannelId,
        }
        connect_payload = {
            "cmd": CHZZK_CHAT_CMD['connect'],
            "tid": 1,
            "bdy": {
                "uid": self.userIdHash,
                "devType": 2001,
                "accTkn": self.accessToken,
                "auth": "SEND"
            }
        }
        payload = {**default_payload, **connect_payload}
        await self.websocket.send(json.dumps(payload))
        response = await self.websocket.recv()
        response_data = json.loads(response)
        self.sid = response_data['bdy']['sid']
        self.logger.info(f'{self.channelName} 채팅창 연결 중... SID: {self.sid}')

        # 최근 채팅 내역 요청
        request_payload = {
            "cmd": CHZZK_CHAT_CMD['request_recent_chat'],
            "tid": 2,
            "sid": self.sid,
            "bdy": {
                "recentMessageCount": 50
            }
        }
        payload = {**default_payload, **request_payload}
        await self.websocket.send(json.dumps(payload))
        await self.websocket.recv()  # 응답 대기 (내용 사용 안 함)
        self.logger.info(f'{self.channelName} 채팅창 연결 완료')

    async def send(self, message: str):
        """웹소켓을 통해 채팅 메시지를 전송합니다."""
        default_payload = {
            "ver": "2",
            "svcid": "game",
            "cid": self.chatChannelId,
        }
        extras = {
            "chatType": "STREAMING",
            "emojis": "",
            "osType": "PC",
            "extraToken": self.extraToken,
            "streamingChannelId": self.chatChannelId
        }
        send_payload = {
            "tid": 3,
            "cmd": CHZZK_CHAT_CMD['send_chat'],
            "retry": False,
            "sid": self.sid,
            "bdy": {
                "msg": message,
                "msgTypeCode": 1,
                "extras": json.dumps(extras),
                "msgTime": int(datetime.datetime.now().timestamp())
            }
        }
        payload = {**default_payload, **send_payload}
        await self.websocket.send(json.dumps(payload))

    async def run(self):
        """메시지 수신 및 Kafka 전송 루프를 비동기로 처리합니다."""
        await self.start_producer()
        await self.connect()

        try:
            while True:
                try:
                    raw_message = await self.websocket.recv()
                except websockets.exceptions.ConnectionClosed:
                    self.logger.error("웹소켓 연결 종료. 재연결 시도...")
                    await self.connect()
                    continue
                except Exception as e:
                    self.logger.error(f"웹소켓 수신 오류: {e}")
                    continue

                try:
                    raw_message = json.loads(raw_message)
                except Exception as e:
                    self.logger.error(f"메시지 JSON 파싱 오류: {e}")
                    continue

                chat_cmd = raw_message.get('cmd')
                if chat_cmd == CHZZK_CHAT_CMD['ping']:
                    pong_payload = {
                        "ver": "2",
                        "cmd": CHZZK_CHAT_CMD['pong']
                    }
                    await self.websocket.send(json.dumps(pong_payload))
                    # 채널 ID가 변경되었는지 확인 (예: 방송 시작 시)
                    if self.chatChannelId != api.fetch_chatChannelId(self.streamer, self.cookies):
                        await self.connect()
                    continue

                if chat_cmd == CHZZK_CHAT_CMD['chat']:
                    chat_type = '채팅'
                elif chat_cmd == CHZZK_CHAT_CMD['donation']:
                    chat_type = '후원'
                else:
                    continue

                for chat_data in raw_message.get('bdy', []):
                    if chat_data.get('uid') == 'anonymous':
                        nickname = '익명의 후원자'
                    else:
                        try:
                            profile_data = json.loads(chat_data.get('profile', '{}'))
                            nickname = profile_data.get("nickname")
                            if 'msg' not in chat_data:
                                continue
                        except Exception as e:
                            self.logger.error(f"프로필 데이터 파싱 오류: {e}")
                            continue

                    timestamp = chat_data.get('msgTime', 0) / 1000.0
                    now = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    msg_text = chat_data.get("msg", "")
                    await self.send_kafka_msg(self.channelName, now, chat_type, nickname, msg_text)
                    self.logger.info(f'[{self.channelName}][{now}][{chat_type}] {nickname} : {msg_text}')
        finally:
            await self.stop_producer()
            await self.websocket.close()


def get_logger():
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("AsyncChzzkChatLogger")
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler('chat.log', mode="w", encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--streamer_id', type=str, default='cd04c50c6ff488ac96f8900e26e5b993',
                        help="Streamer ID")
    #parser.add_argument('--cookies', type=str, default='/app/cookies.json', help="쿠키 파일 경로 (JSON 형식)")
    parser.add_argument('--cookies', type=str, default='cookies.json', help="쿠키 파일 경로 (JSON 형식)")
    parser.add_argument('--broker', type=str, default=None, help="Kafka 브로커 주소")
    args = parser.parse_args()

    with open(args.cookies, 'r', encoding='utf-8') as f:
        cookies = json.load(f)

    logger = get_logger()
    chat_client = AsyncChzzkChat(args.streamer_id, cookies, logger, args.broker)
    await chat_client.run()


if __name__ == '__main__':
    asyncio.run(main())
