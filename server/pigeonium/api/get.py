import requests
from pigeonium.config import Config
from pigeonium.currency import Currency
from pigeonium.transaction import Transaction
from . import responseType

class GET:
    @staticmethod
    def networkInfo() -> responseType.NetworkInfo:
        response = requests.get(Config.ServerUrl)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        response = response.json()
        infoDict:responseType.NetworkInfo = {"NetworkName":response["NetworkName"],
        "BaseCurrencyName":response["BaseCurrencyName"],"BaseCurrencySymbol":response["BaseCurrencySymbol"],"GenesisIssuance":int(response["GenesisIssuance"]),
        "AdminPublicKey":bytes.fromhex(response["AdminPublicKey"]),"LatestIndexId":int(response["LatestIndexId"]),"previous":bytes.fromhex(response["previous"])}
        return infoDict

    @staticmethod
    def balance(address: bytes = None, currencyId: bytes = None, cuIdDict = False, onlyAmount = False) -> list[responseType.BalanceDict] | dict[bytes, int]:
        """
        Returns:
            when cuIdDict = False

            response: list[dict[str, str]]
            - address (bytes)
            - currencyId (bytes)
            - amount (int)

            when cuIdDict = True

            response: dict[bytes, int]
            - key is currencyId
            - value is amount
        """
        params = {}
        if currencyId:
            params["currencyId"] = currencyId.hex()
        if address:
            params["address"] = address.hex()
        response = requests.get(Config.ServerUrl+"balance",params)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        responseJson = response.json()
        if cuIdDict:
            responseDict:dict[bytes, int] = {}
            if currencyId:
                responseDict[currencyId] = 0
            for balanceD in responseJson:
                responseDict[bytes.fromhex(balanceD['currencyId'])] = int(balanceD['amount'])
            return responseDict
        elif onlyAmount:
            if responseJson:
                for balanceD in responseJson:
                    return int(balanceD['amount'])
            else:
                return 0
        else:
            responseList:list[responseType.BalanceDict] = []
            for balanceD in responseJson:
                responseList.append({"address": bytes.fromhex(balanceD['address']), "currencyId": bytes.fromhex(balanceD['currencyId']), "amount": int(balanceD['amount'])})
            return responseList

    @staticmethod
    def currency(currencyId: bytes) -> Currency | None:
        params = {"currencyId": currencyId.hex()}
        response = requests.get(Config.ServerUrl+"currency",params)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        responseJson = response.json()
        if responseJson:
            responseCu = Currency.create(responseJson["name"], responseJson["symbol"],
                                         bytes.fromhex(responseJson["issuer"]), bytes.fromhex(responseJson["inputData"]), int(responseJson["supply"]))
            return responseCu
        else:
            return None

    @staticmethod
    def currencies(sortBy: str = "id", sortOrder: str = "ASC") -> list[Currency]:
        params = {"sortBy": sortBy, "sortOrder": sortOrder}
        response = requests.get(Config.ServerUrl+"currencies",params)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        responseJson = response.json()
        currencyList:list[Currency] = []
        for responseCu in responseJson:
            cu = Currency.create(responseCu["name"], responseCu["symbol"],bytes.fromhex(responseCu["issuer"]),
                                 bytes.fromhex(responseCu["inputData"]), int(responseCu["supply"]))
            currencyList.append(cu)
        return currencyList
    
    @staticmethod
    def transaction(transactionId: bytes = None, indexId: int = 0):
        if transactionId:
            params = {"transactionId": transactionId.hex()}
        else:
            params = {"indexId": indexId}
        response = requests.get(Config.ServerUrl+"transaction",params)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        resTx = response.json()
        if resTx:
            tx = Transaction()
            tx.indexId = int(resTx["indexId"])
            tx.transactionId = bytes.fromhex(resTx["transactionId"])
            tx.timestamp = int(resTx["timestamp"])
            tx.source = bytes.fromhex(resTx["source"])
            tx.dest = bytes.fromhex(resTx["dest"])
            tx.currencyId = bytes.fromhex(resTx["currencyId"])
            tx.amount = int(resTx["amount"])
            tx.publicKey = bytes.fromhex(resTx["publicKey"])
            tx.adminSignature = bytes.fromhex(resTx["adminSignature"])
            return tx
        else:
            return None

    @staticmethod
    def transactions(indexIdFrom:int=None, currencyId:bytes=None, address:bytes=None, source:bytes=None, dest:bytes=None, volume:int = 0) -> list[Transaction]:
        params = {}
        responses = []
        if indexIdFrom:
            params["indexIdFrom"] = indexIdFrom
        if currencyId:
            params["currencyId"] = currencyId.hex()
        if address:
            params["address"] = address.hex()
        if source:
            params["source"] = source.hex()
        if dest:
            params["dest"] = dest.hex()
        params['volume'] = volume

        response = requests.get(Config.ServerUrl+"transactions",params)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        resTxs = response.json()
        for resTx in resTxs:
            tx = Transaction()
            tx.indexId = int(resTx["indexId"])
            tx.transactionId = bytes.fromhex(resTx["transactionId"])
            tx.timestamp = int(resTx["timestamp"])
            tx.source = bytes.fromhex(resTx["source"])
            tx.dest = bytes.fromhex(resTx["dest"])
            tx.currencyId = bytes.fromhex(resTx["currencyId"])
            tx.amount = int(resTx["amount"])
            tx.previous = bytes.fromhex(resTx["previous"])
            tx.publicKey = bytes.fromhex(resTx["publicKey"])
            tx.adminSignature = bytes.fromhex(resTx["adminSignature"])
            responses.append(tx)
        return responses

    @staticmethod
    def previousTxId():
        response = requests.get(Config.ServerUrl)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        previousId = bytes.fromhex(response.json()["previous"])
        return previousId
