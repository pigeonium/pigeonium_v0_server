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

class SwapPoolInfo(TypedDict):
    reserveBaseCurrency: int
    reservePairCurrency: int
    swapFee: int
    history: list[str,str|int]
