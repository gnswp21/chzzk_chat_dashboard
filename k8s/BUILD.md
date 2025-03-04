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

## 치지직 크롤러 빌드

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


# spark
helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
kubectl create namespace spark
helm install spark-operator spark-operator/spark-operator --namespace spark --create-namespace --set sparkJobNamespace=default


# 로드밸런서 컨트롤러
로들밸런서를 외부로 연결하기 위해 로드밸랜서 컨트롤러(LBC)가 필요하다.
다음을 준비한다.
1. sa(쿠버네티스 오브젝트)가  aws의 IAM 사용할 수 있도록 OIDC 설정
2. LB IAM 정책을 가진 sa(로드밸런서컨트롤러를 사용할) 생성
3. Helm으로 LBC 생성 

## 1.sa(쿠버네티스 오브젝트)가  aws의 IAM 사용할 수 있도록 OIDC 설정

```
EKS_NAME=wonderful-dubstep-rainbow
eksctl utils associate-iam-oidc-provider --cluster $EKS_NAME --approve
```


## 2. LB IAM 정책을 가진 sa 생성

```
eksctl create iamserviceaccount \
  --cluster $EKS_NAME \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --attach-policy-arn arn:aws:iam::691487686124:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve
```

## 3. helm eks LBC 설치

```
helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$EKS_NAME \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```