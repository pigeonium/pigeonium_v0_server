from hashlib import sha256

class Server:
    rootPath:str = ""
    port:int = 14513
    txResponseLimit:int = 200
    currenciesResponseLimit:int = 300
    webhookURLs:list[str] = []

class Network:
    AdminPrivateKey:bytes = sha256(b"114514").digest()
    NetworkName:str = "Pigeonium_v0"
    BaseCurrencyName:str = "Pigeon"
    BaseCurrencySymbol:str = "pigeon"
    BaseCurrencyIssuance:int = 1000
    superiorAddress:list[bytes] = [bytes.fromhex("77b1f31c8c067ab01adc53e8a1723a66")]
    SwapWalletPrivateKey:bytes = sha256(b"swap").digest()
 
class MySQL:
    host:str = "localhost"
    port:int = 3306
    user:str = "pigeonium"
    password:str = "password"
    database:str = "pigeonium_v0"
