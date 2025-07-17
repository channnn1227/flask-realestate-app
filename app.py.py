from flask import Flask, render_template
import requests
import xml.etree.ElementTree as ET
import datetime

app = Flask(__name__)
SERVICE_KEY = "Ey6bVfRVh4Cq1rGSFXGB0CwrvjExVFojpYYkv+VTYJDhV52GrxrzmhM2ydvKtcdq4ehvHxmW9dXKY00VvYzg=="
LAWDCODE = "4128112300"

def fetch_real_estate_data(region_code, year_month):
    url = "https://apis.data.go.kr/1613000/AptTradeInfoService1/getTradeAptDetail"
    params = {
        "serviceKey": SERVICE_KEY,
        "LAWD_CD": region_code,
        "DEAL_YMD": year_month,
        "numOfRows": 100
    }
    res = requests.get(url, params=params)
    root = ET.fromstring(res.content)
    items = root.findall(".//item")

    results = []
    for item in items:
        area = float(item.findtext("전용면적", "0"))
        if 83 <= area <= 85:
            results.append({
                "apartment": item.findtext("아파트", "-"),
                "area": f"{area:.2f}",
                "price": item.findtext("거래금액", "-").strip(),
                "floor": item.findtext("층", "-"),
                "date": f"{item.findtext('년')}.{item.findtext('월')}.{item.findtext('일')}"
            })
    return results

@app.route("/deals")
def show_deals():
    today = datetime.date.today()
    data = []
    for i in range(12):  # 최근 12개월
        ym = (today - datetime.timedelta(days=30 * i)).strftime("%Y%m")
        data += fetch_real_estate_data(LAWDCODE, ym)
    return render_template("deals.html", deals=data)

@app.route("/")
def home():
    return "<h1>실거래가 웹앱에 오신 것을 환영합니다!</h1><p><a href='/deals'>실거래가 보기</a></p>"

if __name__ == "__main__":
    app.run(debug=True)
