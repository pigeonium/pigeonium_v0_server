from .utils import Utils

class Currency:
    def __init__(self) -> None:
        self.currencyId:bytes
        self.name:str
        self.symbol:str
        self.inputData:bytes
        self.issuer:bytes
        self.supply:int
    
    def __str__(self):
        idhex = self.currencyId.hex()
        return f"<Currency {self.name}({self.symbol}): {idhex[:6]}....{idhex[-6:]}>"
    
    def __repr__(self):
        return self.__str__()

    @classmethod
    def create(cls,name:str,symbol:str,issuer:bytes,inputData:bytes = bytes(),supply:int=0):
        cu = cls()
        cu.currencyId = Utils.md5(Utils.sha256(name.encode()+symbol.encode()+inputData+issuer))
        cu.name = name
        cu.symbol = symbol
        cu.inputData = inputData
        cu.issuer = issuer
        cu.supply = supply
        return cu
    
    def verify(self):
        try:
            if Utils.md5(Utils.sha256(self.name.encode()+self.symbol.encode()+self.inputData+self.issuer)) == self.currencyId:
                return True
            else:
                return False
        except:
            return False
