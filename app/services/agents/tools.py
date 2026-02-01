from langchain_core.tools import Tool
import pandas as pd
import PyPDF2
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import json
import pandas as pd
import numpy as np
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


class AnalysisTools:
    """데이터 분석 도구"""

    @staticmethod
    def calculate_statistics(data: str) -> str:
        """기본 통계 계산"""
        try:
            df = pd.DataFrame(json.loads(data))
            numeric_cols = df.select_dtypes(include=[np.number]).columns

            stats = {}
            for col in numeric_cols:
                stats[col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                }

            return json.dumps({"success": True, "statistics": stats})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    @staticmethod
    def detect_trends(data: str, time_column: str, value_column: str) -> str:
        """트렌드 감지"""
        try:
            df = pd.DataFrame(json.loads(data))
            df[time_column] = pd.to_datetime(df[time_column])
            df = df.sort_values(time_column)

            # 단순 선형 회귀로 트렌드 계산
            x = np.asarray(len(df), dtype=float)
            y = np.asarray(df[value_column].values, dtype=float)
            slope = np.polyfit(x, y, 1)[0]

            trend = (
                "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            )

            return json.dumps(
                {
                    "success": True,
                    "trend": trend,
                    "slope": float(slope),
                    "change_percentage": float((y[-1] - y[0]) / y[0] * 100),
                }
            )
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    @staticmethod
    def find_outliers(data: str, column: str) -> str:
        """이상치 탐지 (IQR 방법)"""
        try:
            df = pd.DataFrame(json.loads(data))
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]

            return json.dumps(
                {
                    "success": True,
                    "outliers_count": len(outliers),
                    "outliers": outliers.to_dict("records"),
                    "bounds": {
                        "lower": float(lower_bound),
                        "upper": float(upper_bound),
                    },
                }
            )
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})


def create_analysis_tools() -> List[Tool]:
    """분석 도구 생성"""
    return [
        Tool(
            name="calculate_statistics",
            func=AnalysisTools.calculate_statistics,
            description="데이터의 기본 통계량을 계산합니다. 입력: JSON 형식의 데이터",
        ),
        Tool(
            name="detect_trends",
            func=lambda x: AnalysisTools.detect_trends(*x.split("|||")),
            description="시계열 데이터의 트렌드를 감지합니다. 입력: 'data|||time_column|||value_column'",
        ),
        Tool(
            name="find_outliers",
            func=lambda x: AnalysisTools.find_outliers(*x.split("|||")),
            description="데이터에서 이상치를 찾습니다. 입력: 'data|||column'",
        ),
    ]
