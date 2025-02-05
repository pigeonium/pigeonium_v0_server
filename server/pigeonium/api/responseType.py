from typing import TypedDict

class NetworkInfo(TypedDict):
    NetworkName: str
    BaseCurrencyName: str
    BaseCurrencySymbol: str
    GenesisIssuance: int
    AdminPublicKey: bytes
    LatestIndexId: int
    previousTxId: bytes
    SwapPoolAddress: bytes

class BalanceDict(TypedDict):
    address: bytes
    currencyId: bytes
    amount: int
