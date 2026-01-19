import requests

headers = {
    "Authorization": "Bearer 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",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# 1. Tech DB 생성
url = "https://api.notion.com/v1/databases"
payload = {
    "parent": {"page_id": "2e890113889080ae94a2ff72e9cadd4c"},
    "title": [{"text": {"content": "Tech"}}],
    "properties": {  # 이전에 생성한 속성 그대로
        "Name": {"title": {}}
        # ... 전체 속성
    },
}
response = requests.post(url, headers=headers, json=payload)
db_id = response.json()["id"]
print(f"Tech DB 생성: {db_id}")

# 2. 새 프로젝트 추가
url = "https://api.notion.com/v1/pages"
payload = {
    "parent": {"database_id": "PROJECTS_DB_ID"},
    "properties": {
        "Name": {"title": [{"text": {"content": "RAG 앱 개발"}}]},
        "Status": {"select": {"name": "To Do"}},
    },
}
response = requests.post(url, headers=headers, json=payload)
