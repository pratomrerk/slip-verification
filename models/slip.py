import os
import cv2

# pratomrerk
# update 2023-01-31

class slip:

    def qr_decoder(image_path):
        img = cv2.imread(image_path)
        qrDecoder = cv2.QRCodeDetector()
        data, bbox, straight_qrcode = qrDecoder.detectAndDecode(img)
        if data:
            return data
        else:
            return None

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