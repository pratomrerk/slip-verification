## Getting started
View docker-compose.example for an example to docker-compose.yml and edit the environment variables.

## Environment variables
apiportal : https://apiportal.kasikornbank.com/app/my-app
Add a new app and retrieve the app details, including the CONSUMER ID and CONSUMER SECRET.

edit docker-compose.yml
KBANK_CONSUMER_ID=<CONSUMER ID>
KBANK_CONSUMER_SECRET=<CONSUMER SECRET>

## Install
docker-compose up -d --build slip-verification

## Usage
Get slip miniQR information
```bash
curl --location --request POST 'http://127.0.0.1:9111' --form 'slip-image=@"/D:/slip.jpg"'
```

Example Response
```json
{
    "data": {
        "API_ID": "000001",
        "COUNTRY_CODE": "TH",
        "CRC_CHECKSUM": "AAAA",
        "CRC_IS_MATCH": 1,
        "MINI_QR_DATA": "AAAAAAAAA",
        "DATE": "0000-01-01",
        "REF_ID": "AAAAAAAAA",
        "SENDING_BANK_ID": "014",
        "SENDING_BANK_NAME": "Siam Commercial Bank",
        "TRACEID": "AAAAAAAAA"
    },
    "statusCode": 200
}
```

Verify slip
```bash
curl --location --request POST 'http://127.0.0.1:9111/verify' \
--header 'Content-Type: application/json' \
--data-raw '{
    "sending_bank_id" : "<SENDING_BANK_ID>",
    "trans_ref" : "<REF_ID>"
}'
```

Example Response
```json
{
  "rqUID": "783_20191108_v4UIS1K2Mobile",
  "kbankTxnId": "rrt-6584062560186912337-b-gse1-20836-48028137-3",
  "statusCode": "0000",
  "statusMessage": "SUCCESS",
  "data": {
    "language": "TH",
    "transRef": "010092101507665143",
    "sendingBank": "004",
    "receivingBank": "004",
    "transDate": "20200401",
    "transTime": "10:15:07",
    "sender": {
      "displayName": "นาย ธนาคาร ก",
      "name": "Mr. Thanakarn K",
      "proxy": {
        "type": null,
        "value": null
      },
      "account": {
        "type": "BANKAC",
        "value": "xxx-x-x0209-x"
      }
    },
    "receiver": {
      "displayName": "กสิกร ร",
      "name": "KASIKORN R",
      "proxy": {
        "type": "",
        "value": ""
      },
      "account": {
        "type": "BANKAC",
        "value": "xxx-x-x3109-x"
      }
    },
    "amount": 1,
    "paidLocalAmount": 1,
    "paidLocalCurrency": "764",
    "countryCode": "TH",
    "transFeeAmount": 0,
    "ref1": "",
    "ref2": "",
    "ref3": "",
    "toMerchantId": ""
  }
}
```