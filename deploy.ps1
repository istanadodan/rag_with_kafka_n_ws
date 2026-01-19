## Docker image 생성
docker build . -t local-registry:5000/rag-api:0.1.0

### Docker image를 local docker registry에 등록
docker push local-registry:5000/rag-api:0.1.0

### K8s에 배포
kubectl rollout restart deployment rag-api -n rag