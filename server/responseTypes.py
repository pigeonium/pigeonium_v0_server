from pydantic import BaseModel
from typing import Literal

class NetworkInfo(BaseModel):
    NetworkName:str
    PigeoniumVersion:int
    BaseCurrencyName:str
    BaseCurrencySymbol:str
    GenesisIssuance:int
    AdminPublicKey:str
    LatestIndexId:int
    networkId:int
    SwapPoolAddress:str

class Balance(BaseModel):
    address:str
    currencyId:str
    amount:int

class Transaction(BaseModel):
    indexId:int
    transactionId:str
    timestamp:int
    source:str
    dest:str
    currencyId:str
    amount:int
    networkId:int
    publicKey:str
    adminSignature:str

class SwapHistory(BaseModel):
    swapType:Literal['buy','sell']
    inputAmount:int
    outputAmount:int
    timestamp:int

class SwapInfo(BaseModel):
    reserveBaseCurrency:int
    reservePairCurrency:int
    swapFee:int
    history:SwapHistory
