import hashlib
import requests
from typing import overload
from decimal import Decimal

class Utils:
    @staticmethod
    def dictFormat(data: dict):
        for dKey in list(data.keys()):
            dValue = data[dKey]
            if type(dValue) == bytes:
                data[dKey] = dValue.hex()
            elif type(dValue) == int:
                data[dKey] = str(dValue)
        return data
    
    @staticmethod
    def hex2bytes(hex: str, length: int = None) -> bytes:
        b = bytes.fromhex(hex)
        if length and len(b) < length:
            b = bytes(length - len(b)) + b
        return b
    
    @overload
    @staticmethod
    def convertAmount(amount: int) -> str:
        pass

    @overload
    @staticmethod
    def convertAmount(amount: float) -> int:
        pass

    @staticmethod
    def convertAmount(amount):
        if isinstance(amount, int):
            dec = Decimal(amount) / 1000000
            return str(dec)
        elif isinstance(amount, float):
            dec = Decimal(str(amount)) * 1000000
            return int(dec)
        else:
            raise ValueError()
    
    @staticmethod
    def contraction(bytesObj: bytes, length: int = 6):
        hexObj = bytesObj.hex()
        return f"{hexObj[:length]}....{hexObj[-length:]}"

    @staticmethod
    def sha256(string: bytes) -> bytes:
        return hashlib.sha256(string).digest()

    @staticmethod
    def md5(string: bytes) -> bytes:
        return hashlib.md5(string).digest()

    @staticmethod
    def get(url: str, params: dict):
        response = requests.get(url, params)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def post(url: str, data: dict):
        response = requests.post(url, data)
        response.raise_for_status()
        return response.json()
