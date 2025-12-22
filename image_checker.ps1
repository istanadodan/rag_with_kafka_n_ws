# docker run --rm -it local-registry:5000/rag-api:0.1.0 `
#   python - << 'EOF'
# import sys
# print(sys.path)
# EOF

docker run --rm -it local-registry:5000/rag-api:0.1.0 `
  python -c "import sys; print(sys.path)"


docker run --rm -it local-registry:5000/rag-api:0.1.0 `
  python -c "import os; print(os.listdir('/app'))"


# docker run --rm -it local-registry:5000/rag-api:0.1.0 `
#   python -c "import core.config; print('OK')"

# docker run --rm -it local-registry:5000/rag-api:0.1.0 `
#   python -c "import core.config; print(dir(core.config))"
