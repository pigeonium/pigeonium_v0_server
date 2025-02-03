from .utils import Utils
from .wallet import Wallet
from .config import Config

class Currency:
    def __init__(self) -> None:
        self.currencyId:bytes
        self.name:str
        self.symbol:str
        self.inputData:bytes
        self.issuer:bytes
        self.publicKey:bytes
        self.supply:int
        self.issuerSignature:bytes
    
    def __str__(self):
        idhex = self.currencyId.hex()
        return f"<Currency {self.name}({self.symbol}): {idhex[:6]}....{idhex[-6:]}>"
    
    def __repr__(self):
        return self.__str__()

    @classmethod
    def create(cls,name:str,symbol:str,issuerWallet:Wallet,inputData:bytes = bytes(),supply:int=0):
        cu = cls()
        cu.currencyId = Utils.md5(Utils.sha256(name.encode()+symbol.encode()+inputData+issuerWallet.address))
        cu.name = name
        cu.symbol = symbol
        cu.inputData = inputData
        cu.issuer = issuerWallet.address
        cu.supply = supply
        cu.issuerSignature = issuerWallet.sign(cu.currencyId)
        return cu
    
    def verify(self):
        try:
            issuerWallet = Wallet.fromPublic(self.publicKey)
            if self.currencyId == bytes(16):
                if issuerWallet.publicKey != Config.AdminPublicKey:
                    return False
            else:
                if Utils.md5(Utils.sha256(self.name.encode()+self.symbol.encode()+self.inputData+issuerWallet.address)) != self.currencyId:
                    return False
            return issuerWallet.verifySignature(self.currencyId,self.issuerSignature)
        except:
            return False
