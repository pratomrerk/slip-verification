import os, sys
import requests
import json
import base64
import cv2
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime as dt
import hashlib
import uuid

# slip verification
# pratomrerk
# update 2023-01-31

app = Flask(__name__)
CORS(app)
root_path = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(root_path, 'upload')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

KBANK_CONSUMER_ID = os.environ.get('KBANK_CONSUMER_ID', 'a2FzaWtvcm5iYW5rdXNlcg==')
KBANK_CONSUMER_SECRET = os.environ.get('KBANK_CONSUMER_SECRET', 'a2FzaWtvcm5iYW5rcGFzc3dvcmQ=')
KBANK_AUTHORIZATION = base64.b64encode(f'{KBANK_CONSUMER_ID}:{KBANK_CONSUMER_SECRET}'.encode()).decode()
KBANK_TEST_MODE = os.environ.get('KBANK_TEST_MODE', 'false')

SENDING_BANK_IDS = {
    '002': 'Bangkok Bank',
    '004': 'Krungthai Bank',
    '006': 'Thai Bank',
    '011': 'TMB Bank',
    '014': 'Siam Commercial Bank',
    '017': 'Citibank',
    '020': 'Standard Chartered',
    '022': 'CIMB Thai',
    '024': 'UOB',
    '025': 'Krungsri Ayudhya',
    '030': 'Aomsin',
    '033': 'Tisco Bank',
    '034': 'TAC Bank',
    '065': 'Thanachart Bank',
    '066': 'Islamic Bank of Thailand',
    '067': 'Tisco Bank',
    '069': 'Kiatnakin Bank',
    '073': 'Land and Houses Bank'
}

USER_AGENT = 'PostmanRuntime/7.26.8'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['KBANK_ACCESS_TOKEN'] = None

def kbank_oauth():
    url = 'https://openapi-sandbox.kasikornbank.com/v2/oauth/token'
    headers = {
        'Authorization': 'Basic ' + KBANK_AUTHORIZATION,
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': USER_AGENT,
    }
    if KBANK_TEST_MODE == 'true':
        headers['x-test-mode'] = 'true'
        headers['env-id'] = 'OAUTH2'
    data = {
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        print('Error: kbank_oauth')
        print(response.text)
        return None

def kbank_verify(user, slip):
    url = 'https://openapi-sandbox.kasikornbank.com/v1/verslip/kbank/verify'
    headers = {
        'Authorization': 'Bearer ' + user['access_token'],
        'Content-Type': 'application/json',
        'User-Agent': USER_AGENT,
    }
    if KBANK_TEST_MODE == 'true':
        headers['x-test-mode'] = 'true'
    print(headers)
    rqUID = str(uuid.uuid1())
    # ISO 8601 format
    rqDt = dt.datetime.now().isoformat() + '+07:00'
    data = {
        'rqUID': rqUID,
        'rqDt': rqDt,
        'data': {
            'sendingBank' : slip['sending_bank_id'],
            'transRef' : slip['trans_ref'],
        },
    }
    print(data)
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print('Error: kbank_verify')
        print(response.text)
        return None

def slip_image_qr_decoder(image_path):
    img = cv2.imread(image_path)
    qrDecoder = cv2.QRCodeDetector()
    data, bbox, straight_qrcode = qrDecoder.detectAndDecode(img)
    if data:
        return data

def crc_iso13239(data, poly=0x1021, init=0xffff, xor_out=0xffff):
    crc = init
    for byte in data:
        crc = crc ^ (byte << 8)
        for i in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc = crc << 1
    return crc & xor_out

def get_field(data: str) -> str:
    try:
        id = data[0:2]
        length = int(data[2:4])
        payload = data[4:4 + length]
        payload_next = data[4 + length:]
        return id, length, payload, payload_next
    except:
        print('Error: get field : ' + data)
        return '', None, None, None

def allowed_extension(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['POST'])
def slip_info():

    if request.files.get('slip-image') is None:
        return jsonify({
            'statusCode': 400,
            'message': 'slip-image is required'
        })

    # Slip Image QR Code
    file = request.files['slip-image']
    if file and allowed_extension(file.filename) == False:
        return jsonify({
            'statusCode': 400,
            'message': 'slip-image must be image file'
        })

    #file md5
    file_md5 = hashlib.md5(file.read()).hexdigest()
    slip_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file_md5 + '.jpg')
    file.seek(0)
    file.save(slip_image_path)
    file.close()

    mini_qr_data = slip_image_qr_decoder(slip_image_path)

    info = {}
    #test_data = '0046000600000101030140225202301299A6KPki5w0SLXn2685102TH91048BBD'
    info['MINI_QR_DATA'] = mini_qr_data

    # Payload
    id00, length00, payload00, payload_next = get_field(mini_qr_data)
    if id00 == '00':
        subid00, sublength00, API_ID, next = get_field(payload00)
        info['API_ID'] = API_ID
        subid01, sublength01, BANK_ID, next = get_field(next)
        info['SENDING_BANK_ID'] = BANK_ID
        if BANK_ID in SENDING_BANK_IDS:
            info['SENDING_BANK_NAME'] = SENDING_BANK_IDS[BANK_ID]
        else:
            info['SENDING_BANK_NAME'] = 'Unknown'
        subid02, sublength02, REF_ID, next = get_field(next)
        info['REF_ID'] = REF_ID
        yyyymmdd = REF_ID[0:8]
        info['DATE'] = yyyymmdd[0:4] + '-' + yyyymmdd[4:6] + '-' + yyyymmdd[6:8]
        info['TRACEID'] = REF_ID[8:sublength02]
    else:
        print('Error: ID00 not found')
        return jsonify({
            'statusCode': 400,
            'message': 'Error: ID00 not found'
        })

    # Country Code
    id51, length51, payload51, payload_next = get_field(payload_next)
    if id51 == '51':
        info['COUNTRY_CODE'] = payload51
    else:
        print('Error: ID51 not found')
        return jsonify({
            'statusCode': 400,
            'message': 'Error: ID51 not found'
        })

    # CRC
    id91, length91, payload91, payload_next = get_field(payload_next)
    if id91 == '91':
        #info['CRC_INT'] = int(payload91, 16)
        #info['CRC'] = payload91
        checksum = mini_qr_data[-4:]
        data_byte = bytearray(mini_qr_data[0:-4].encode())
        crc = crc_iso13239(data_byte)
        crc_hex = hex(crc)[2:].upper()
        is_match = 0
        if crc_hex == checksum:
           is_match = 1
        info['CRC_CHECKSUM'] = crc_hex
        info['CRC_IS_MATCH'] = is_match
    else:
        print('Error: ID91 not found')
        return jsonify({
            'statusCode': 400,
            'message': 'Error: ID91 not found'
        })

    print('---- Slip Verification ----')
    for key, value in info.items():
        print(f'{key} : {value}')
    print('-' * 30)

    return jsonify({
        'statusCode': 200,
        'data': info
    })

@app.route('/verify', methods=['POST'])
def verifier():
    
    timestamp = dt.datetime.timestamp(dt.datetime.now())

    # check expire
    if app.config['KBANK_ACCESS_TOKEN'] is not None:
        user = app.config['KBANK_ACCESS_TOKEN']
        if timestamp >= user['expires']:
            app.config['KBANK_ACCESS_TOKEN'] = None

    if app.config['KBANK_ACCESS_TOKEN'] is None:
        user = kbank_oauth()
        if user is None:
            return jsonify({
                'statusCode': 400,
                'message': 'Error: bank access'
            })
        user['expires'] = timestamp + int(user['expires_in'])
        app.config['KBANK_ACCESS_TOKEN'] = user
    
    user = app.config['KBANK_ACCESS_TOKEN']
    #print(user)
    data = request.get_json()

    if 'sending_bank_id' not in data:
        return jsonify({
            'statusCode': 400,
            'message': 'sending_bank_id is required'
        })
    
    if 'trans_ref' not in data:
        return jsonify({
            'statusCode': 400,
            'message': 'trans_ref is required'
        })

    if data['sending_bank_id'] not in SENDING_BANK_IDS:
        return jsonify({
            'statusCode': 400,
            'message': 'sending_bank_id is invalid'
        })

    response = kbank_verify(user, data)
    if response is None:
        return jsonify({
            'statusCode': 400,
            'message': 'Error: bank verify'
        })

    return jsonify(response)

if __name__ == '__main__':

    app.run(port=9111, debug=True)
    
