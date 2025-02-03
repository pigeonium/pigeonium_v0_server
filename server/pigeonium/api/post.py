import requests
from pigeonium.config import Config
from pigeonium.currency import Currency
from pigeonium.transaction import Transaction
from pigeonium.wallet import Wallet

class POST:
    @staticmethod
    def transaction(transaction: Transaction):
        postData = {"transactionId": transaction.transactionId.hex(),"dest":transaction.dest.hex(),
                    "currencyId":transaction.currencyId.hex(),"amount":transaction.amount,"publicKey":transaction.publicKey.hex()}
        response = requests.post(Config.ServerUrl+"transaction",json=postData)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        response = response.json()
        transaction.indexId = int(response["indexId"])
        transaction.timestamp = int(response["timestamp"])
        transaction.adminSignature = bytes.fromhex(response["adminSignature"])
        return transaction

    @staticmethod
    def issuance(currency: Currency, amount: int, issuerWallet: Wallet, senderWallet: Wallet):
        senderSign = senderWallet.sign(currency.currencyId)
        postData = {"currencyId":currency.currencyId.hex(), "name":currency.name, "symbol":currency.symbol, "inputData":currency.inputData.hex(),
                    "amount":amount, "issuerSignature":currency.issuerSignature.hex(), "publicKey":issuerWallet.publicKey.hex(),
                    "senderPublicKey":senderWallet.publicKey.hex(), "senderSignature":senderSign.hex()}
        response = requests.post(Config.ServerUrl+"issuance",json=postData)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        response = response.json()

        responseTx = Transaction.fromDict(response)

        return responseTx
