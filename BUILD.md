쿠버네티스에 strimizi operator 설치

# 카프카

```
helm repo add strimzi https://strimzi.io/charts/
helm repo update
kubectl create namespace kafka
helm install strimzi-kafka-operator strimzi/strimzi-kafka-operator --namespace kafka

kubectl apply kafka/kafka-broker.yaml
``` 


## 카프카 프로듀서 및 브로커 연결 테스트
docker build -t debug -f dockerfiles/producer/Dockerfile dockerfiles/producer

## 치지직 크롤러 빌드드

docker build -t chzzk_producer -f Dockerfile .
docker tag chzzk_producer:latest 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com/chzzk_producer:latest
docker push 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com/chzzk_producer:latest


# aws ecr

aws ecr create-repository --repository-name chzzk_producer --region ap-northeast-2

docker exec dreamy_tu aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com

docker tag debug:latest 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com/chzzk_producer:latest
docker push 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com/chzzk_producer:latest

kubectl apply -f temp/temp.yaml

# 푸시한것
실험


###
kubectl exec my-cluster-kafka-0 -n kafka -- bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic debug-topic --from-beginning