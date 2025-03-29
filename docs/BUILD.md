# 도커 클라언트
cd k8s
docker compose up -d
docker exec -it client bash



# aws
## eks 생성
eksctl create cluster \
  --name $EKS_NAME \
  --region ap-northeast-2 \
  --with-oidc \
  --instance-types=m5.xlarge \
  --managed \
  --profile default \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 2 \
  --node-volume-size 40 \
  --version 1.31

## ebs csi driver 설치
eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster $EKS_NAME \
  --region ap-northeast-2

## AWS IAM 권한부여
- chzzk (client 컨테이너에 aws 계정)
  - ClusterAdmin

### nodegroup ebs를 위한 ec2FullAccess
```
# nodegroup 명 조회
NG=$(aws eks list-nodegroups --cluster-name $EKS_NAME --query "nodegroups[0]" --output text)

# iam policy 명 조회
ARN=$(aws eks describe-nodegroup --cluster-name $EKS_NAME --nodegroup-name $NG --query "nodegroup.nodeRole" --output text)
ARN_NAME=${ARN##*/}

# ec2 full access 추가
aws iam attach-role-policy --role-name $ARN_NAME --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess
```


# helm
## 카프카

helm repo add strimzi https://strimzi.io/charts/
helm repo update
kubectl create namespace kafka
helm install strimzi-kafka-operator strimzi/strimzi-kafka-operator --namespace kafka

## spark

helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update
helm install spark-operator spark-operator/spark-operator --namespace spark-operator --create-namespace


# aws ecr image

## ecr producer
docker run client -n client
docker build -t producer -f ../cpd/producer/Dockerfile ../cpd/producer

docker exec client aws ecr create-repository --repository-name chzzk_producer --region ap-northeast-2
docker exec client aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com

docker tag producer:latest 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com/chzzk_producer:latest
docker push 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com/chzzk_producer:latest

## consumer
docker build -t consumer -f ../cpd/consumer/Dockerfile ../cpd/consumer

docker exec client aws ecr create-repository --repository-name chzzk_consumer --region ap-northeast-2
docker exec client aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com

docker tag consumer:latest 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com/chzzk_consumer:latest
docker push 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com/chzzk_consumer:latest

## web
docker build -t web -f ../cpd/web/Dockerfile ../cpd/web

docker exec client aws ecr create-repository --repository-name chzzk_web --region ap-northeast-2
docker exec client aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com

docker tag web:latest 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com/chzzk_web:latest
docker push 691487686124.dkr.ecr.ap-northeast-2.amazonaws.com/chzzk_web:latest


# kafka
kubectl apply -f build/kafka/kafka-broker.yaml

# mysql
kubectl apply -f build/aws/ebs_storage.yaml
kubectl apply -f build/mysql/mysql.yaml


# producer
kubectl delete secret json-secret
kubectl create secret generic json-secret \
  --from-file=build/producer/secret/

kubectl delete -f build/producer/chzzk_producer.yaml
kubectl apply -f build/producer/chzzk_producer.yaml


# consumer(spark)
kubectl apply -f build/consumer/rbac.yaml
kubectl apply -f build/consumer/spark.yaml

# web
kubectl apply -f build/web/web.yaml

# monitoring prometheus grafana

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.service.type=LoadBalancer



### delete

eksctl delete cluster --name $EKS_NAME --profile default




# 모니터링
## 각 db 저장된 데이터 크기기
SELECT table_schema AS 'Database', 
       ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables 
GROUP BY table_schema;


## 각 테이블 마다 쌓인 로우수
SELECT table_name, table_rows 
FROM information_schema.tables
WHERE table_schema = 'mydb';