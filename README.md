# Kafka기반 비동기 RAG Pipeline POC

### Docker image 생성

docker build . -t local-registry:5000/rag-api:0.1.0

### Docker image를 local docker registry에 등록

docker push local-registry:5000/rag-api:0.1.0

### K8s에 배포

1. 배포 제거
   kdf .\deployment.yaml
2. 배포
   kaf .\deployment.yaml

### port-forward 설정

1. qdrant db: 10->6333
   kubectl port-forward service/qdrantdb -n rag 10:6333
   ==> Ingress 설정으로 변경

   1. host: rag-api.local #sub-domain생성
   2. path: /
   3. pathType: PreFix
   4. Service: qdrantdb:6333

2. rag-api: 5 -> 8000
   kubectl port-forward service/rag-api -n rag 5:8000
   ==> Ingress 설정으로 변경
   1. path: /rag-api
   2. pathType: PreFix
   3. service: rag-api:8000
   4. proxy-body-size: 100m 추가 설정

### 로깅

- kubectl get pod -n rag|sls rag-api
- kubectl logs -n rag rag-api-7c69f7c577-9xldf -f

kubectl get pod -n rag |sls rag-api|% {kubectl logs -f ($\_.line.Split()[0]) -n rag}

## kafka

topic:
rag_ingestion_start
