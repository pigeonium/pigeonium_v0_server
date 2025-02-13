from ecdsa import VerifyingKey, NIST256p
import hashlib
from .utils import Utils
from .config import Config
from .wallet import Wallet

class Transaction:
    def __init__(self) -> None:
        self.indexId:int = None
        self.transactionId:bytes = None
        self.timestamp:int = None
        self.source:bytes = None
        self.dest:bytes = None
        self.currencyId:bytes = None
        self.amount:int = None
        self.networkId:int = None
        self.publicKey:bytes = None
        self.adminSignature:bytes = None
    
    def __str__(self):
        txIdHex = self.transactionId.hex()
        sourceHex = self.source.hex()
        destHex = self.dest.hex()
        return f"<Transaction {txIdHex[:6]}....{txIdHex[-6:]} | {sourceHex[:6]}....{sourceHex[-6:]} --> {destHex[:6]}....{destHex[-6:]}>"
    
    def __repr__(self):
        return self.__str__()

    @classmethod
    def create(cls,wallet:Wallet,dest:bytes,currencyId:bytes,amount:int):
        tx = cls()
        tx.transactionId = wallet.sign(dest + currencyId + amount.to_bytes(8, 'big') + Config.NetworkId.to_bytes(8, 'big'))
        tx.source = wallet.address
        tx.dest = dest
        tx.currencyId = currencyId
        tx.amount = amount
        tx.networkId = Config.NetworkId
        tx.publicKey = wallet.publicKey
        return tx
    
    def verify(self):
        if (not (self.source == Utils.md5(Utils.sha256(self.publicKey))) and not (self.source == bytes(16))):
            return False, False
        try:
            if self.source == bytes(16):
                public_key = VerifyingKey.from_string(Config.AdminPublicKey,NIST256p,hashlib.sha256)
            else:
                public_key = VerifyingKey.from_string(self.publicKey,NIST256p,hashlib.sha256)
            data = (self.dest + self.currencyId + self.amount.to_bytes(8, 'big') + self.networkId.to_bytes(8, 'big'))

            if public_key.verify(self.transactionId,data):
                sourceSign = True
            else:
                sourceSign = False
        except:
            sourceSign = False
        try:
            public_key = VerifyingKey.from_string(Config.AdminPublicKey,NIST256p,hashlib.sha256)
            if public_key.verify(self.adminSignature,(self.indexId.to_bytes(8, 'big') + self.transactionId + self.timestamp.to_bytes(8, 'big') + self.networkId.to_bytes(8, 'big'))):
                adminSign = True
            else:
                adminSign = False
        except:
            adminSign = False
        return sourceSign, adminSign
    
    def adminConfirm(self, indexId:int, txTimestamp:int, adminWallet:Wallet):
        signature = adminWallet.sign(indexId.to_bytes(8, 'big') + self.transactionId + txTimestamp.to_bytes(8, 'big') + self.networkId.to_bytes(8, 'big'))
        self.indexId = indexId
        self.timestamp = txTimestamp
        self.adminSignature = signature
    
    def toDict(self):
        txDict = {}
        txDict['indexId'] = self.indexId
        txDict['transactionId'] = self.transactionId
        txDict['timestamp'] = self.timestamp
        txDict['source'] = self.source
        txDict['dest'] = self.dest
        txDict['currencyId'] = self.currencyId
        txDict['amount'] = self.amount
        txDict['networkId'] = self.networkId
        txDict['publicKey'] = self.publicKey
        txDict['adminSignature'] = self.adminSignature
        return txDict

    @classmethod
    def fromDict(cls, transaction: dict):
        tx = cls()
        tx.indexId = transaction.get('indexId', None)
        tx.transactionId = transaction.get('transactionId', None)
        tx.timestamp = transaction.get('timestamp', None)
        tx.source = transaction.get('source', None)
        tx.dest = transaction.get('dest', None)
        tx.currencyId = transaction.get('currencyId', None)
        tx.amount = transaction.get('amount', None)
        tx.networkId = transaction.get('networkId', None)
        tx.publicKey = transaction.get('publicKey', None)
        tx.adminSignature = transaction.get('adminSignature', None)
        return tx
