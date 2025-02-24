쿠버네티스에 strimizi operator 설치

# 카프카

```
helm repo add strimzi https://strimzi.io/charts/
helm repo update
kubectl create namespace kafka
helm install strimzi-kafka-operator strimzi/strimzi-kafka-operator --namespace kafka
``` 


## 카프카 프로듀서 및 브로커 연결 테스트


# aws ecr

