from langchain_core.tools import Tool
import pandas as pd
import PyPDF2
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import json


class DataCollectionTools:
    """데이터 수집을 위한 도구 모음"""

    @staticmethod
    def read_csv_file(file_path: str) -> str:
        """CSV 파일 읽기"""
        try:
            df = pd.read_csv(file_path)
            return json.dumps(
                {
                    "success": True,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "text_preview": df.head(5).to_dict(),
                    "dtypes": df.dtypes.astype(str).to_dict(),
                }
            )
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    @staticmethod
    def read_excel_file(file_path: str) -> str:
        """Excel 파일 읽기"""
        try:
            df = pd.read_excel(file_path)
            return json.dumps(
                {
                    "success": True,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "text_preview": df.head(5).to_dict(),
                    "dtypes": df.dtypes.astype(str).to_dict(),
                }
            )
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    @staticmethod
    def extract_pdf_text(file_path: str) -> str:
        """PDF에서 텍스트 추출"""
        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return json.dumps(
                {
                    "success": True,
                    "pages": len(reader.pages),
                    "text_preview": text[:500],
                }
            )
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    @staticmethod
    def scrape_web_data(url: str) -> str:
        """웹 페이지에서 데이터 추출"""

        def _fetch_article(url: str) -> str:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            encoding_char = response.apparent_encoding

            if "charset=" not in response.headers.get("content-type", ""):
                encoding_char = "utf-8"

            response.encoding = encoding_char
            return response.text

        try:
            html = _fetch_article(url)
            soup = BeautifulSoup(html, "html.parser")

            # 테이블 추출
            tables = []
            for table in soup.find_all("table")[:3]:  # 최대 3개
                df = pd.read_html(str(table))[0]
                tables.append(df.to_dict())

            # 텍스트 추출
            article = soup.find("article")
            text = article.get_text().replace("\n\n", "") if article else ""

            return json.dumps(
                {
                    "success": True,
                    "tables_found": len(tables),
                    "tables": tables,
                    "text_preview": text,
                },
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})


def create_data_collection_tools() -> list[Tool]:
    """데이터 수집 도구 생성"""
    return [
        Tool(
            name="read_csv",
            func=DataCollectionTools.read_csv_file,
            description="CSV 파일을 읽고 메타데이터를 반환합니다. 입력: 파일 경로",
        ),
        Tool(
            name="read_excel",
            func=DataCollectionTools.read_excel_file,
            description="Excel 파일을 읽고 메타데이터를 반환합니다. 입력: 파일 경로",
        ),
        Tool(
            name="extract_pdf",
            func=DataCollectionTools.extract_pdf_text,
            description="PDF 파일에서 텍스트를 추출합니다. 입력: 파일 경로",
        ),
        Tool(
            name="scrape_web",
            func=DataCollectionTools.scrape_web_data,
            description="웹 페이지에서 테이블과 텍스트를 추출합니다. 입력: URL",
        ),
    ]
