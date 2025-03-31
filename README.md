### 프로젝트 개요

CHZZK Chat Dashboard는 웹소켓을 통한 실시간 채팅 데이터 수집부터, Kafka 기반 메시지 중계, Spark 스트리밍 처리, 그리고 Streamlit 대시보드 배포까지의 End-to-End 데이터 파이프라인을 구축한 프로젝트입니다.  
이 프로젝트는 AWS EKS 상에서 Kubernetes 기반의 분산 처리 클러스터로 운영되며, 로컬 디버깅 환경을 구성해 클라우드 비용을 절감할 수 있도록 설계되었습니다.

![img](/docs/img/실시간메시지집계.png)

- [채널 리스트](/k8s/build/producer/secret/)

- [배포중](http://ab9493a099da741b5b03ca167340c759-1161361867.ap-northeast-2.elb.amazonaws.com/)


### 주요 특징 및 성능 지표

#### End-to-End 데이터 파이프라인 구성

- **데이터 수집:** 웹소켓을 통해 분당 평균 **30,000건** 이상의 채팅 메시지를 수집
- **메시지 중계:** Apache Kafka를 활용해 수집된 데이터를 **5초 이내**로 중계
- **실시간 처리:** Apache Spark 스트리밍을 이용해 **5분 단위 집계 처리** 수행
- **데이터 시각화:** Streamlit 대시보드에서 **5초 이내**로 업데이트된 결과 제공

#### 분산 처리 클러스터 (AWS EKS 기반)

- Kubernetes 환경에서 채널 수집을 **10개 이상의 파드**로 구성되어 안정적인 분산 처리를 지원
- 자동화 도구 및 k8s 커뮤니티 기능 활용으로 **배포 시간을 30% 단축**
- 쿠버네티스를 통해 **수평 확장 및 장애 복구(셀프 힐링)** 기능 적용

#### 로컬 디버깅 및 클라우드 비용 최적화

- 로컬 환경에서 Kubernetes와 동일한 설정으로 디버깅 가능
- 동일 코드 베이스를 컨테이너로 패키징하여 클라우드 배포에 바로 활용
- 클라우드 비용을 절감할 수 있는 환경 구성

### 시스템 아키텍처

![img](/docs/img/architecture.png)

#### 데이터 수집 (Producer)

- 웹소켓을 통해 채팅 데이터를 실시간 수집
- 수집된 데이터는 Kafka Producer를 통해 Kafka 브로커로 전송

#### 메시지 중계 (Kafka)

- Apache Kafka를 활용해 데이터 흐름을 분리 및 비동기 처리
- 다수의 소비자(Consumer)가 동일 데이터를 병렬로 처리할 수 있도록 지원

#### 실시간 처리 (Consumer)

- Apache Spark 스트리밍을 이용해 Kafka 메시지를 실시간으로 처리 및 집계
- 처리 결과를 MySQL 등 관계형 데이터베이스에 저장

#### 데이터 시각화 (Dashboard)

- Streamlit을 활용해 집계된 데이터를 실시간 대시보드로 시각화
- 사용자 친화적인 UI로 최신 채팅 데이터 및 통계 정보 제공

#### 배포 및 인프라 관리

- Docker 컨테이너로 각 서비스 패키징
- AWS EKS 상에서 Kubernetes를 활용해 각 컨테이너 배포 및 자동화 관리
- Helm 차트를 이용해 Kafka, Spark Operator 등 핵심 컴포넌트 설치

### 기술 스택

- **프로그래밍 언어:** Python
- **프레임워크:** Spark, Kafka
- **데이터베이스:** Mysql, Mongo
- **기타:** Docker, k8s, AWS EKS

# Feature

## 프로듀서 파드

데이터 수집단에 해당하는 프로듀서는 기존에 존재하던 1개의 채널에 대한 데이터를 수집하는 [비공식 API](https://github.com/Buddha7771/ChzzkChat?tab=readme-ov-file)를 활용했습니다.

비동기 IO로 기존의 API를 수정 후 20개 이상의 채널에서 채팅 메세지를 받아오는 것으로 다중 채널에 대한 데이터 수집을 실시합니다.

또한, 해당 프류듀서를 k8s 스테이트풀셋으로 만들어 10개의 파드에서 작동해 최종적으로 200개 이상의 채널에 대한 데이터를 실시간 수집하게 만들었습니다.

한 파드에서 200개 채널을 수집하는 경우보다, 파드에 가해지는 자원부담은 줄어 초기 파드 실행이 빠르고 장애 발생시 장애 파드를 제외한 파드에는 문제가 발생하지 않는 장점을 얻을 수 있었습니다.

## 부하 테스트

헬름과 그라파나 스택을 통해 각 파드의 자원 소모량을 측정 했습니다.
각 프로듀서 파드는 시간대에 따라 8,000명 ~ 15,000의 시청자가 생성하는 채팅을 가져와 브로커에게 전송하는 역할을 갖습니다.

![alt text](/docs/img/팔로워수_채널그룹핑.png)

- 메모리사용
  ![alt text](/docs/img/memory.png)

- CPU 사용
  ![alt text](/docs/img/cpu.png)

프로젝트 진행 중 주요 자원부하는 _채널의 시청자수_ 보다는 *연결하는 채널의 수*가 많을 수록 더 큰 부하가 발생하는 것을 확인했습니다.

- 네트워크 사용
  ![alt text](/docs/img/net.png)

## 디렉토리 구조 및 빌드

### cpd

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

### k8s

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

### 빌드

- 준비
  - eks 생성 권한이 있는 aws IAM user, 해당 user의 credentials를 /k8s/config/password.txt 에 저장
- [Build.md](/docs/BUILD.md)를 참고해 "client" 도커 컨테이너를 통해 eks 생성, 각 오퍼레이터 및 k8s 객체 생성

# 주요 디버그

자세한 디버그 내역은 [Debug.md](/docs/Debug.md)에서 확인할 수 있습니다.

# 향후 로드맵

## 모니터링

- 모니터링 수단 추가
  - [x] 프로메테우스, 그라파나 추가
    - 추가됨

## 보안 및 인증

- 웹소켓 방식으로 가져오는 채팅창. 현재 개인 유저의 웹 쿠키가 필요
  - 이 쿠키를 갱신시킬 수 있는 방법 고안

## 프로듀서

- 더 많은 채널의 채팅창을 연결
  - [x] 현재 5 채널이지만 더 많은 채팅창을 연결 후
    - 한 파드당 20개에서 40개의 채널을 연결하도록 수정 (비동기 IO를 통해 가능해짐) (25/03/31)
  - 이를 위해 부하 테스트 와 그에 따른 파드 및 노드 증설

## 대시보드

- 더 다양한 대쉬보드 기능 제공
  - 채널명 검색에 대한 피드백 제공 (없는 채널, 비슷한 채널명)
  - 기간별 검색 기능
  - 유저에게 채팅에 따른 채널 점수 제공
  - 시청자수 대비 채팅 비율 제공
  - 채팅을 이용한 통계 제공
    - 현재 가장 많은 채팅을 치고 있는 채널
    - 일주일간 가장 많은 채팅이 있는 채널
    - 특정 채널의 채팅을 가장 많이 친 사용자

## 안정성, 데이터 퀄리티 및 정합성

- 데이터 수집 및 처리에 안정성 및 정합성 테스트
  - 실시간으로 수집되는 데이터의 총 개수 \*
  - 네트워크 사용량 측정 \*
  - 데이터 유실율율 검사
  - 데이터 퀄리티 검사
    - 모든 데이터에 타임스탬프가 있는가?
    - 모든 데이터에 닉네임, 메세지가 있는가?

## Acknowledgements

본 프로젝트의 치지직 채팅 데이터를 가져오는 API 구현은 [Buddha7771/ChzzkChat](https://github.com/Buddha7771/ChzzkChat?tab=readme-ov-file)의 코드를 참고하여 작성되었습니다. 해당 오픈소스 자료에 감사드리며, 자세한 내용과 라이선스 정보는 원본 레포지토리를 참조해 주시기 바랍니다.
