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
            return str(f"{amount / 1000000:,.6f}".rstrip('0').rstrip('.'))
        elif isinstance(amount, float):
            return int(Decimal(str(amount)) * 1000000)
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

    class inputData:
        @staticmethod
        def readFile(filePath: str) -> bytes:
            with open(filePath, "rb") as f:
                fileData = f.read()
            filePthSplit = filePath.split(".")
            if len(filePthSplit) == 1 or len(filePthSplit[-1]) >= 5:
                fileType = "bin"
            else:
                fileType = filePthSplit[-1]
            inputData = fileType.encode() + bytes(3) + fileData
            return inputData
        
        @staticmethod
        def writeFile(inputData: bytes, filePath: str = "./output"):
            inputHex = inputData.hex()
            fileType, fileData = inputHex.split("000000", 1)
            with open(f"{filePath}.{bytes.fromhex(fileType).decode()}", "wb") as f:
                f.write(bytes.fromhex(fileData))
