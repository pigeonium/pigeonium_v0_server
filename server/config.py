def hex2bytes(hex: str, length:int = None) -> bytes:
    b = bytes.fromhex(hex)
    if length and len(b) < length:
        b = bytes(length - len(b)) + b
    return b

class Node:
    port:int = 14510
    txResponseLimit:int = 200
    currenciesResponseLimit:int = 300

class Network:
    AdminPrivateKey:bytes = hex2bytes("114514",length=32)
    NetworkName:str = "Pigeonium_v0"
    BaseCurrencyName:str = "Pigeon"
    BaseCurrencySymbol:str = "pigeon"
    BaseCurrencyIssuance:int = 1000
    AllowedIssuanceSenderAddress:list[bytes] = [hex2bytes("456738b895b3e30397eb3b394dca545f",16)]

class MySQL:
    host:str = "localhost"
    port:int = 3306
    user:str = "pigeonium"
    password:str = "password"
    database:str = "pigeonium_v0"
