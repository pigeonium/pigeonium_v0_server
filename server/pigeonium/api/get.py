import requests
from pigeonium.config import Config
from pigeonium.currency import Currency
from pigeonium.transaction import Transaction
from . import responseType
from typing import Literal

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
        "AdminPublicKey":bytes.fromhex(response["AdminPublicKey"]),"LatestIndexId":int(response["LatestIndexId"]),"networkId":int(response["networkId"]),
        "SwapPoolAddress":bytes.fromhex(response["SwapPoolAddress"])}
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
            responseCu = Currency()
            responseCu.currencyId = responseJson['currencyId']
            responseCu.name,responseCu.symbol = responseJson['name'],responseJson['symbol']
            responseCu.issuer = bytes.fromhex(responseJson['issuer'])
            responseCu.inputData,responseCu.issuerSignature = bytes.fromhex(responseJson['inputData']),bytes.fromhex(responseJson['issuerSignature'])
            responseCu.publicKey = bytes.fromhex(responseJson['publicKey'])
            return responseCu
        else:
            return None

    @staticmethod
    def currencies(sortBy: str = "id", sortOrder: Literal["ASC","DESC"] = "ASC") -> list[Currency]:
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
            cu = Currency()
            cu.currencyId = bytes.fromhex(responseCu['currencyId'])
            cu.name,cu.symbol = responseCu['name'],responseCu['symbol']
            cu.issuer = bytes.fromhex(responseCu['issuer'])
            cu.supply = int(responseCu['supply'])
            cu.inputData,cu.issuerSignature = bytes.fromhex(responseCu['inputData']),bytes.fromhex(responseCu['issuerSignature'])
            cu.publicKey = bytes.fromhex(responseCu['publicKey'])
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
            tx.networkId = int(resTx["networkId"])
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
            tx.networkId = int(resTx["networkId"])
            tx.publicKey = bytes.fromhex(resTx["publicKey"])
            tx.adminSignature = bytes.fromhex(resTx["adminSignature"])
            responses.append(tx)
        return responses

    @staticmethod
    def swapEstimatedOutput(swapType: Literal["buy","sell"], currencyId: bytes, inputAmount: int):
        if not (swapType == "buy" or swapType == "sell"):
            raise ValueError("Only 'buy' or 'sell' can be entered in 'swapType'")
        
        response = requests.get(Config.ServerUrl+f"swap/{currencyId.hex()}")
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        
        if swapType == "buy":
            reserve_InputCurrency, reserve_OutputCurrency = int(response.json()['reserveBaseCurrency']), int(response.json()['reservePairCurrency'])
        else:
            reserve_OutputCurrency, reserve_InputCurrency = int(response.json()['reserveBaseCurrency']), int(response.json()['reservePairCurrency'])
        
        swapFee = int(response.json()['swapFee'])

        fee_multiplier = 1000 - swapFee
        effective_input = (inputAmount * fee_multiplier) // 1000
        denominator = reserve_InputCurrency + effective_input

        if denominator == 0:
            estimated_output_amount = 0
        else:
            estimated_output_amount = (reserve_OutputCurrency * effective_input) // denominator

        return estimated_output_amount

    @staticmethod
    def swapInfo(currencyId: bytes):
        response = requests.get(Config.ServerUrl+f"swap/{currencyId.hex()}")
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        responseJson = response.json()
        swapHistoryJson = responseJson['history']
        swapHistory = []
        for history in swapHistoryJson:
            swapHistory.append(
                {'swapType': str(history['swapType']),
                 'inputAmount': int(history['inputAmount']),
                 'outputAmount': int(history['outputAmount']),
                 'timestamp': int(history['timestamp'])}
            )
        responseDict:responseType.SwapPoolInfo = {
            'reserveBaseCurrency': int(responseJson['reserveBaseCurrency']),
            'reservePairCurrency': int(responseJson['reservePairCurrency']),
            'swapFee': int(responseJson['swapFee']),
            'history': swapHistory}

        return responseDict

    @staticmethod
    def swaps():
        response = requests.get(Config.ServerUrl+f"swaps")
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        
        responseDict:dict[bytes,responseType.SwapPoolInfo] = {}
        for poolCuId in response.json().keys():
            responseDict[bytes.fromhex(poolCuId)] = {
            'reserveBaseCurrency': int(response.json()['reserveBaseCurrency']),
            'reservePairCurrency': int(response.json()['reservePairCurrency']),
            'swapFee': int(response.json()['swapFee'])}

        return responseDict
