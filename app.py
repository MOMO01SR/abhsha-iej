from flask import Flask, request, jsonify, render_template
import hmac
import hashlib
import time
import requests
import os

app = Flask(__name__)

# يتم استدعاء المفاتيح من بيئة الاستضافة وليس من الكود مباشرة لحمايتها
API_KEY = os.environ.get("BINANCE_API_KEY")
API_SECRET = os.environ.get("BINANCE_SECRET_KEY")
BASE_URL = 'https://api.binance.com'

def get_signature(query_string):
    return hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

# فتح واجهة لوحة التحكم
@app.route('/')
def home():
    return render_template('index.html')

# جلب رصيد USDT
@app.route('/api/balance', methods=['GET'])
def get_balance():
    if not API_KEY or not API_SECRET:
        return jsonify({"balance": "المفاتيح غير متوفرة"}), 400

    timestamp = int(time.time() * 1000)
    query_string = f"timestamp={timestamp}"
    signature = get_signature(query_string)
    
    headers = {'X-MBX-APIKEY': API_KEY}
    url = f"{BASE_URL}/sapi/v1/capital/config/getall?{query_string}&signature={signature}"
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        usdt_balance = next((item for item in data if item["coin"] == "USDT"), None)
        return jsonify({"balance": usdt_balance['free'] if usdt_balance else 0})
    except Exception as e:
        return jsonify({"balance": "خطأ في الاتصال"}), 500

# الإرسال الجماعي (يتطلب تفعيل Merchant وصلاحيات Payout من بينانس)
@app.route('/api/bulk_send', methods=['POST'])
def bulk_send():
    req_data = request.json
    users = req_data.get('users')
    amount_per_user = req_data.get('amount')
    
    if not users or not amount_per_user:
        return jsonify({"error": "بيانات مفقودة"}), 400

    results = []
    for uid in users:
        timestamp = int(time.time() * 1000)
        # رابط ومعلمات Binance Pay Payout API (تأكدي من توثيق بينانس الأحدث)
        query_string = f"timestamp={timestamp}&receiveType=PAY_ID&receiveId={uid}&amount={amount_per_user}&currency=USDT"
        signature = get_signature(query_string)
        
        headers = {'X-MBX-APIKEY': API_KEY}
        url = f"https://bpay.binanceapi.com/binancepay/openapi/payout/transfer?{query_string}&signature={signature}"
        
        # ملاحظة: هذا السطر مكمم (محاكاة) لمنع الإرسال الفعلي بالخطأ أثناء التجربة. 
        # عند التأكد من حساب التاجر الخاص بك، أزيلي علامة # من السطرين التاليين:
        # response = requests.post(url, headers=headers)
        # results.append({"uid": uid, "status": response.status_code})
        
        results.append({"uid": uid, "status": "تمت المحاكاة بنجاح", "amount": amount_per_user})
        
    return jsonify({"message": "تمت معالجة الطلبات", "details": results})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
