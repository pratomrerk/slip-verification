import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime as dt
import hashlib
import random
from models.slip import slip
from models.scb import scb
from models.kbank import kbank

# slip verification
# pratomrerk
# update 2023-01-31

app = Flask(__name__)
CORS(app)
root_path = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(root_path, 'upload')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
USER_AGENT = 'Slip-Verification/1.0'

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

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

    # slip image qr code
    file = request.files['slip-image']
    if file and allowed_extension(file.filename) == False:
        return jsonify({
            'statusCode': 400,
            'message': 'slip-image must be image file'
        })

    # get file md5
    file_md5 = hashlib.md5(file.read()).hexdigest()

    # create upload path
    now = dt.datetime.now()
    dir_ymd = ['%Y', '%m', '%d']
    upload_path = app.config['UPLOAD_FOLDER']
    for d in dir_ymd:
        upload_path = os.path.join(upload_path, now.strftime(d))
        if not os.path.exists(upload_path):
            os.mkdir(upload_path)

    # slip image save
    slip_image_path = os.path.join(upload_path, file_md5 + '.jpg')
    file.seek(0)
    file.save(slip_image_path)
    file.close()

    # read qr code
    mini_qr_data = slip.qr_decoder(slip_image_path)

    info = {}
    #test_data = '0046000600000101030140225202301299A6KPki5w0SLXn2685102TH91048BBD'
    info['MINI_QR_DATA'] = mini_qr_data

    # Payload
    id00, length00, payload00, payload_next = slip.get_field(mini_qr_data)
    if id00 == '00':
        subid00, sublength00, API_ID, next = slip.get_field(payload00)
        info['API_ID'] = API_ID
        subid01, sublength01, BANK_ID, next = slip.get_field(next)
        info['SENDING_BANK_ID'] = BANK_ID
        if BANK_ID in SENDING_BANK_IDS:
            info['SENDING_BANK_NAME'] = SENDING_BANK_IDS[BANK_ID]
        else:
            info['SENDING_BANK_NAME'] = 'Unknown'
            print('[+] New Bank ID: ' + BANK_ID)
        subid02, sublength02, REF_ID, next = slip.get_field(next)
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
    id51, length51, payload51, payload_next = slip.get_field(payload_next)
    if id51 == '51':
        info['COUNTRY_CODE'] = payload51
    else:
        print('Error: ID51 not found')
        return jsonify({
            'statusCode': 400,
            'message': 'Error: ID51 not found'
        })

    # CRC
    id91, length91, payload91, payload_next = slip.get_field(payload_next)
    if id91 == '91':
        #info['CRC_INT'] = int(payload91, 16)
        #info['CRC'] = payload91
        checksum = mini_qr_data[-4:]
        data_byte = bytearray(mini_qr_data[0:-4].encode())
        crc = slip.crc_iso13239(data_byte)
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

    sending_bank_id = data['sending_bank_id']
    trans_ref = data['trans_ref']

    response = None
    use_banks = os.environ.get('USE_BANKS', 'KBANK,SCB').split(',')
    use_banks = random.sample(use_banks, len(use_banks))
    for bank in use_banks:
        if os.environ.get('USE_' + bank, '1') == '0':
            use_banks.remove(bank)
    
    for bank in use_banks:
        if response is not None:
            break
        if bank == 'SCB':
            bank = scb(USER_AGENT)
        if bank == 'KBANK':
            bank = kbank(USER_AGENT)
        response = bank.verifier(sending_bank_id, trans_ref)

    if response is not None:
        return jsonify(response)
    else:
        return jsonify({
            'statusCode': 400,
            'message': 'Error: bank verify'
        })

if __name__ == '__main__':

    app.run(port=9111, debug=True)
    
