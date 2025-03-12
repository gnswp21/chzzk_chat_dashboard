# aws
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

콘솔 root ClusterAdmin
nodegroup IAM에 ec2FullAceess 추가


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


# aws

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

# monogo
kubectl apply -f build/mongo/mongo.yaml

# producer
kubectl create secret generic json-secret \
  --from-file=build/producer/cookies.json \
  --from-file=build/producer/channel_list.json

kubectl apply -f build/producer/chzzk_producer.yaml
# consumer(spark)
kubectl apply -f build/consumer/rbac.yaml
kubectl apply -f build/consumer/spark.yaml

# web
kubectl apply -f build/web/web.yaml




### delete

eksctl delete cluster --name $EKS_NAME --profile default


