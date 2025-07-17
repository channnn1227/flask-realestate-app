import requests
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import xml.etree.ElementTree as ET

app = Flask(__name__)

# ★★★★★ 1단계: 본인의 실제 API 키를 여기에 입력하세요 ★★★★★
KAKAO_API_KEY = "d513459fed9ef1d35fff8f4d4683e586"
GO_DATA_API_KEY = "Ey6bVfRVh4C0Cq1rGSFXGB0CwrvjExVFojpYYkv+VTYJDhV52GrxrzmhM2ydvKtcdq4ehvHxmW9dXKY00VvYzg=="
KAKAO_JS_KEY_FOR_HTML = "efc55d84df34922094681d91d24bf86d"
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

# 카카오 키워드 -> 좌표 및 주소 변환 API
def get_coords_from_address(address):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": address}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200 and response.json()['documents']:
        doc = response.json()['documents'][0]
        if doc.get('road_address_name'):
            address_detail_url = "https://dapi.kakao.com/v2/local/search/address.json"
            address_params = {"query": doc['road_address_name']}
            address_response = requests.get(address_detail_url, headers=headers, params=address_params)
            if address_response.status_code == 200 and address_response.json()['documents']:
                address_doc = address_response.json()['documents'][0]
                if address_doc.get('address') and address_doc['address'].get('b_code'):
                     return {"lat": float(doc['y']), "lng": float(doc['x']), "b_code": address_doc['address']['b_code']}
    return None

# 국토교통부 실거래가 조회 API
def get_real_estate_transactions(b_code, deal_ymd):
    url = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev"
    params = {"serviceKey": GO_DATA_API_KEY, "LAWD_CD": b_code, "DEAL_YMD": deal_ymd, "numOfRows": "50"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        try:
            root = ET.fromstring(response.content)
            transactions = []
            for item in root.findall('.//item'):
                transactions.append({
                    "price": f"{item.find('거래금액').text.strip()}만원",
                    "apt_name": item.find('아파트').text.strip(),
                    "area": f"{float(item.find('전용면적').text.strip()):.2f}㎡",
                    "date": f"{item.find('년').text.strip()}년 {item.find('월').text.strip()}월 {item.find('일').text.strip()}일"
                })
            return transactions
        except ET.ParseError: return []
    return []

@app.route('/')
def index():
    return render_template('index.html', KAKAO_JS_KEY=KAKAO_JS_KEY_FOR_HTML)

@app.route('/search', methods=['POST'])
def search():
    address = request.form.get('address')
    if not address: return jsonify({"error": "주소가 입력되지 않았습니다."}), 400
    location_info = get_coords_from_address(address)
    if not location_info: return jsonify({"error": "유효하지 않은 주소이거나 변환에 실패했습니다."}), 404
    today = datetime.now()
    transactions = []
    for i in range(12):
        month_offset = today.month - i; year_offset = today.year
        if month_offset <= 0: month_offset += 12; year_offset -= 1
        deal_ymd = f"{year_offset}{month_offset:02d}"; transactions.extend(get_real_estate_transactions(location_info['b_code'], deal_ymd))
    unique_transactions = [dict(t) for t in {tuple(d.items()) for d in transactions}]
    return jsonify({"center": {"lat": location_info['lat'], "lng": location_info['lng']}, "transactions": sorted(unique_transactions, key=lambda x: x['date'], reverse=True)})

if __name__ == '__main__':
    app.run(debug=True)
