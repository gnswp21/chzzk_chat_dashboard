# CHZZK_CHAT_DASHBOARD

![img](/docs/img/실시간메시지집계.png)

치지직 채팅 내역을 실시간 수집해 다양한 채팅정보를 제공하는 대쉬보드 운영

- [채널 리스트](/k8s/build/producer/secret/)
- [배포](http://a5a09b8fb24a5420da53195eec142574-793482572.ap-northeast-2.elb.amazonaws.com)

## 주요 기능

![img](/docs/img/메시지검색.png)

- **기능 1:** 특정 채널의 채팅 메시지를 5분 단위로 그룹화하여, 최근 25분간의 채팅 건수를 집계·제공하는 기능
- **기능 2:** 특정 채널의 특정 닉네임의 유저가 작성한 채팅 내역 제공
- **기능 3:** 특정 채널에서 메세지 내용을 바탕으로 채팅 내역 제공
- **기능 4:** AWS ELB를 통해 채팅 내역 대쉬보드를 클러스터 외부로 배포

# 프로젝트 아키텍쳐

![img](/docs/img/architecture.png)

## 기술 스택

- **프로그래밍 언어:** Python
- **프레임워크:** Spark, Kafka
- **데이터베이스:** Mysql
- **기타:** Docker, k8s, AWS EKS

## 메커니즘

- 데이터 수집 : 치치직 채널에 웹소켓 방식을 통해 연결하여, 채팅 내역을 가져옵니다.
- 데이터 중계: 수집된 데이터를 카프카 브로커로 전송합니다.
- 데이터 처리 : 스파크 스트림을 통해 카프카 브로커로 전송된 채팅 데이터를 mysql로 저장합니다.
- 데이터 마트: Streamlit과 pymysql을 통해 mysql에 저장된 데이터를 요청에 따라 집계 후 개시합니다.

# 부하 테스트

헬름과 그라파나 스택을 통해 각 파드의 자원 소모량을 측정 했습니다.
각 파드는 1천명 ~ 9천명의 시청자가 생성하는 채팅을 가져와 브로커에게 전송하는 역할을 갖습니다.

![alt text](/docs/img/viewers.png)

- 메모리사용
  ![alt text](/docs/img/memory.png)

- CPU 사용
  ![alt text](/docs/img/cpu.png)

프로젝트 진행 중 주요 자원부하는 _채널의 시청자수_ 보다는 *연결하는 채널의 수*가 많을 수록 더 큰 부하가 발생하는 것을 확인했습니다.

- 네트워크 사용
  ![alt text](/docs/img/net.png)

# 디렉토리 구조 및 빌드드

## cpd

치지직 라이브 정보, 프로듀서, 컨슈머, 웹 대쉬보드에 대한 소스 코드 및 도커파일

- chzzk
  - fetch_live_info.py : 치지직 라이브 정보 패치
  - sort*channels.py : 라이브 정보를 통해 100명 이상의 시청장를 보유한, channel_list*[n].json 10개 생성 . 해당 채널 리스트는 프로듀서 파드에 각각 분배되어 프로듀서 파드들이 최대한 균등한 부하를 받도록 구성
- producer

  - ChzzkChatAPI : 기존에 사용되던 비공식 Chzzk Chat API를 약간 변형하여 사용
  - kafka_producer.py : ChzzkChatAPI를 실행하는 실행파일

- consumer

  - spark_streaming_consumer.py : spark streaming을 통해 kafka 'chzzk' 토픽에 들어오는 메시지(채팅)을 mysql로 실시간 저장

- web
  - web.py : streamlit을 이용해 사용자가 검색한 채널에 대해 채팅수 변화, 채팅 DB를 제공합니다

## k8s

- build : 각 k8s 객체에 대한 manifest 파일
  - aws : ebs stroage class
  - consumer
  - kafka
  - mongo : -
  - mysql
  - producer
    - _secret_ : chzzk-producer 파드가 연결하는 채널 리스트가 담겨있습니다.
  - web
- config:
  - password.txt : client 컨테이너에 사용되는 aws IAM user의 credential

## 빌드

- 준비
  - eks 생성 권한이 있는 aws IAM user, 해당 user의 credentials를 /k8s/config/password.txt 에 저장
- [Build.md](/docs/BUILD.md)를 참고해 "client" 도커 컨테이너를 통해 eks 생성, 각 오퍼레이터 및 k8s 객체 생성

# 주요 디버그

자세한 디버그 내역은 [Debug.md](/docs/Debug.md)에서 확인할 수 있습니다.

# 향후 로드맵

- 모니터링 수단 추가
  - 프로메테우스, 그라파나 추가
  -
- 웹소켓 방식으로 가져오는 채팅창. 현재 개인 유저의 웹 쿠키가 필요
  - 이 쿠키를 갱신시킬 수 있는 방법 고안
- 더 많은 채널의 채팅창을 연결
  - 현재 5 채널이지만 더 많은 채팅창을 연결 후
  - 이를 위해 부하 테스트 와 그에 따른 파드 및 노드 증설
- 더 다양한 대쉬보드 기능 제공

  - 유저에게 채팅에 따른 채널 점수 제공
  - 시청자수 대비 채팅 비율 제공
  - 채팅을 이용한 통계 제공
    - 현재 가장 많은 채팅을 치고 있는 채널
    - 일주일간 가장 많은 채팅이 있는 채널
    - 특정 채널의 채팅을 가장 많이 친 사용자

- 데이터 수집 및 처리에 안정성 및 정합성 테스트
  - 실시간으로 수집되는 데이터의 총 개수 \*
  - 네트워크 사용량 측정 \*
  - 데이터 유실율율 검사
  - 데이터 퀄리티 검사
    - 모든 데이터에 타임스탬프가 있는가?
    - 모든 데이터에 닉네임, 메세지가 있는가?

## Acknowledgements

본 프로젝트의 치지직 채팅 데이터를 가져오는 API 구현은 [Buddha7771/ChzzkChat](https://github.com/Buddha7771/ChzzkChat?tab=readme-ov-file)의 코드를 참고하여 작성되었습니다. 해당 오픈소스 자료에 감사드리며, 자세한 내용과 라이선스 정보는 원본 레포지토리를 참조해 주시기 바랍니다.
