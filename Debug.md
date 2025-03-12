# 서비스 노출 문제

1. 문제 상황
   서비스 외부 노출 실패:
   EKS Auto 모드(주로 Fargate 사용)에서 LoadBalancer 타입의 서비스를 생성했지만, 외부 IP가 할당되지 않고 <pending> 상태로 머물렀습니다.
   AWS Load Balancer Controller(LBC) 미설치 또는 문제:
   외부 로드 밸런서 생성을 위해 LBC가 필요한데, 초기에는 LBC가 설치되어 있지 않았거나, LBC가 CrashLoopBackOff 상태에 빠졌습니다.
   메타데이터 접근 문제:
   LBC의 로그에서 "failed to fetch VPC ID from instance metadata" 오류가 발생했습니다.
   이는 최신 AMI (Bottlerocket, AL2023 등)에서 IMDSv2가 기본으로 적용되면서 토큰 기반 접근이 필요하고, 기본 hop limit이 낮아 VPC ID를 자동으로 감지하지 못해서 발생하는 문제였습니다.
   서브넷 태그 문제:
   외부 로드 밸런서를 생성하려고 할 때, AWS는 올바른 서브넷을 찾기 위해 "kubernetes.io/role/elb" 태그가 있는 공용 서브넷을 요구하는데, 해당 태그가 없거나 일부 서브넷에만 존재하여 문제가 발생했습니다.
2. 시행착오 및 해결 시도
   LBC 설치 및 IRSA 적용:

LBC를 설치하고 IRSA를 적용했으나, LBC 파드가 CrashLoopBackOff 상태에 빠졌고, 로그에서 IMDS를 통한 VPC ID 조회 실패가 확인되었습니다.
VPC ID 직접 지정 시도:

Helm 설치 시 --aws-vpc-id 인자를 추가하여 수동으로 VPC ID를 지정하려고 했지만, 여전히 IMDS 접근을 시도하는 문제가 발생했습니다.
노드의 IMDS 설정 검토:

Bottlerocket이나 AL2023에서 IMDSv2가 기본 적용되어 토큰이 필요하고 hop limit이 낮다는 점이 문제의 핵심임을 확인했습니다.
IMDS 설정(예: hop limit 조정)을 통해 문제를 해결하는 방법도 고려되었지만, 보안 측면에서 위험 요소가 있어 최종 선택은 어려웠습니다.
서브넷 태그 수정:

외부 로드 밸런서를 생성하기 위해 공용 서브넷에 "kubernetes.io/role/elb" 태그를 추가하는 작업도 진행했습니다.
태그가 올바르게 설정되지 않으면, AWS가 적절한 서브넷을 찾지 못해 LB 생성에 실패하게 됩니다.
IAM 권한 확인:

403 에러가 발생한 경우, AWSLoadBalancerControllerIAMPolicy가 최신 권한을 포함하는지, 그리고 연결된 역할에 누락된 권한이 없는지 확인했습니다. 3. 최종 해결 방법
AWS Load Balancer Controller 설치 및 설정 수정:
LBC를 최신 버전으로 설치하고, Deployment YAML 파일을 수정하여 (예: extraArgs 또는 수동 수정) VPC ID를 지정하는 시도를 했으나, IMDS 문제로 인해 여전히 VPC ID 조회 문제가 있었음.
서브넷 태그 수정 및 외부 LB 사용 설정:
외부 서비스를 노출하기 위해 서비스 YAML에 service.beta.kubernetes.io/aws-load-balancer-internal: "false" 애노테이션을 추가하고, 공용 서브넷에 "kubernetes.io/role/elb" 태그를 올바르게 설정함.
결과:
최종적으로 외부 로드 밸런서가 생성되었고, DNS 이름 (예: k8s-default-jupyters-ffc22fd8f1-f24facebb7df9616.elb.ap-northeast-2.amazonaws.com)을 통해 서비스에 접근할 수 있게 되었습니다.+ 추가적으로 모든 서브넷에 해당 태그 추가, http:DNS/tree 로 접근 가능했다.

- SA에 ELB 관련 권한이 부족하다.


# loadbalancer
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


  ## ELB 디버그
- 로드밸런서.yaml에 해당 태그 추가 --aws-vpc-id
  - helm으로 가능할지
- vpc에 모든 서브넷(4개)에 kubernetes.io/role/elb 을 1? 로 설정했던 것 같음음

## EBS 동적 프로비저닝, EBS CSI


### 디버그 - 스파크 컨슈머

kubectl delete sparkapplication spark-streaming-consumer

kubectl apply -f build/consumer/spark.yaml

kubectl describe sparkapplication spark-streaming-consumer

kubectl get sparkapplication


kubectl logs -f spark-streaming-consumer-driver

컨슈머에는 너무 많은 문제가 있었다.

1. eks-auto 모드는 ㅈ비사용중인 리소스를 제거하는데, 스파크와 적합하지 않은 느낌이다
2. eks 설치에 대해 더 이해했다.
   1. eks 콘솔에서는 노드 그룹이 잘 부착이 안된다. gke 때도 그랬는데, 흠 eksctl로 바로 설치하니까 원하는 규격으로 잘 만들어졌다.
   2. 클러스터 어드민 롤 root에도 추가
   3. ebs csi 드라이버 추가
      1. 이를 위해 ec2 풀 엑세스 권한을 노드 그룹에 추가
3. spark-operator 사용에 rbac 기반 sa가 필요하다고 공식문서에 나왔따.(에러 통해 알고 후에 문서 확인)
4. kerberos 에러, name 에서 NPE가 나오는 에러가 발생. 
   1. https://stackoverflow.com/questions/65183714/what-is-the-cause-of-java-lang-nullpointerexception-invalid-null-input-name
   2. 해당 링크에서 도커파일의 USER를 UID 1001로 해놔서 해당 문제가 발생한 것이라고 하였다.
   3. 이를 sparkuser로 명명해 고쳐주니 문제가 해결됐다.