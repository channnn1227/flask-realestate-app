from flask import Flask, render_template, request
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)

def get_real_estate_data():
    url = "http://apis.data.go.kr/1613000/AptLeaseDetailSvc1/getAptLeaseDetail"
    service_key = "Ey6bVfRVh4Cq1rGSFXGB0CwrvjExVFojpYYkv+VTYJDhV52GrxrzmhM2ydvKtcdq4ehvHxmW9dXKY00VvYzg=="
    params = {
        "serviceKey": service_key,
        "LAWD_CD": "41390",  # 시흥시
        "DEAL_YMD": "202507",
        "numOfRows": 100,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        result = []
        for item in items:
            result.append({
                "아파트": item.findtext("아파트"),
                "보증금액": item.findtext("보증금액"),
                "월세금액": item.findtext("월세금액"),
                "전용면적": item.findtext("전용면적"),
                "층": item.findtext("층"),
                "거래금액": item.findtext("거래금액"),
                "도로명": item.findtext("도로명"),
                "거래일자": f"{item.findtext('년')}-{item.findtext('월')}-{item.findtext('일')}",
            })
        return result
    except Exception as e:
        print("API 오류:", e)
        return []

@app.route("/")
def home():
    return "Hello, this is your real estate app!"

@app.route("/deals")
def deals():
    data = get_real_estate_data()
    return render_template("deals.html", items=data)

if __name__ == "__main__":
    app.run(debug=True)
