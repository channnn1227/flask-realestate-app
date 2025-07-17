from flask import Flask, render_template, request
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

app = Flask(__name__)

# 국토부 API 기본 설정
API_URL = "http://apis.data.go.kr/1613000/AptLeaseInfoDetailSvc1/getAptLeaseDetail"
API_KEY = "Ey6bVfRVh4Cq1rGSFXGB0CwrvjExVFojpYYkv+VTYJDhV52GrxrzmhM2ydvKtcdq4ehvHxmW9dXKY00VvYzg=="
LAWD_CODES = {
    "월곶동": "4139031000",
    "배곧동": "4139051000"
}

def fetch_deal_data(lawd_cd, deal_ymd):
    params = {
        "serviceKey": API_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 100
    }

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.content)

        items = []
        for item in root.findall(".//item"):
            apt = {
                "단지명": item.findtext("단지명", default="N/A"),
                "전
