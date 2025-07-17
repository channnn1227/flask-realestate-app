import os
import requests
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import xml.etree.ElementTree as ET

app = Flask(__name__)

# ★★★★★ 중요: 환경 변수에서 API 키를 가져옵니다 ★★★★★
KAKAO_API_KEY = os.getenv('KAKAO_API_KEY')
GO_DATA_API_KEY = os.getenv('GO_DATA_API_KEY')
KAKAO_JS_KEY_FOR_HTML = os.getenv('KAKAO_JS_KEY')
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
                     return {
                        "lat": float(doc['y']),
                        "lng": float(doc['x']),
                        "b_code": address_doc['address']['b_code']
                    }
    return None

# 국토교통부 실거래가 조회 API
def get_real_estate_transactions(b_code, deal_ymd):
    url = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev"
    params = {
        "serviceKey": GO_DATA_API_KEY,
        "LAWD_CD": b_code,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "50"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        try:
            root = ET.fromstring(response.content)
            transactions = []
            for item in root.findall('.//item'):
                price = item.find('거래금액').text.strip()
                apt_name = item.find('아파트').text.strip()
                area = item.find('전용면적').text.strip()
                deal_year = item.find('년').text.strip()
                deal_month = item.find('월').text.strip()
                deal_day = item.find('일').text.strip()
                
                transactions.append({
                    "price": f"{price}만원",
                    "apt_name": apt_name,
                    "area": f"{float(area):.2f}㎡",
                    "date": f"{deal_year}년 {deal_month}월 {deal_day}일"
                })
            return transactions
        except ET.ParseError:
            return []
    return []

@app.route('/')
def index():
    # ★★★★★ 중요: index.html 렌더링 시 환경 변수에서 가져온 키를 전달합니다. ★★★★★
    return render_template('index.html', KAKAO_JS_KEY=KAKAO_JS_KEY_FOR_HTML)

@app.route('/search', methods=['POST'])
def search():
    address = request.form.get('address')
    if not address:
        return jsonify({"error": "주소가 입력되지 않았습니다."}), 400

    location_info = get_coords_from_address(address)
    if not location_info:
        return jsonify({"error": "유효하지 않은 주소이거나 변환에 실패했습니다."}), 404

    today = datetime.now()
    transactions = []
    for i in range(12): # 최근 12개월 데이터 조회
        month_offset = today.month - i
        year_offset = today.year
        if month_offset <= 0:
            month_offset += 12
            year_offset -= 1
        deal_ymd = f"{year_offset}{month_offset:02d}"
        transactions.extend(get_real_estate_transactions(location_info['b_code'], deal_ymd))
    
    unique_transactions = [dict(t) for t in {tuple(d.items()) for d in transactions}]
    
    return jsonify({
        "center": {"lat": location_info['lat'], "lng": location_info['lng']},
        "transactions": sorted(unique_transactions, key=lambda x: x['date'], reverse=True)
    })

if __name__ == '__main__':
    # Render와 같은 프로덕션 환경에서는 이 부분이 직접 실행되지 않습니다.
    # 대신 Gunicorn 같은 웹 서버가 app 객체를 실행합니다.
    app.run(debug=True)
