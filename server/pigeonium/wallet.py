from ecdsa import SigningKey, VerifyingKey, NIST256p
import hashlib
from .utils import Utils

class Wallet:
    def __init__(self) -> None:
        self.privateKey:bytes
        self.publicKey:bytes
        self.address:bytes
    
    def __str__(self) -> str:
        return f"<Wallet {self.address.hex()}>"
    
    def __repr__(self):
        return self.__str__()
    
    @classmethod
    def generate(cls):
        wallet = cls()
        private_key = SigningKey.generate(NIST256p,None,hashlib.sha256)
        public_key = private_key.get_verifying_key().to_string()
        wallet.privateKey = private_key.to_string()
        wallet.publicKey = public_key
        wallet.address = Utils.md5(Utils.sha256(public_key))

        return wallet
    
    @classmethod
    def fromPrivate(cls,privateKey:bytes):
        wallet = cls()
        private_key = SigningKey.from_string(privateKey,NIST256p,hashlib.sha256)
        public_key = private_key.get_verifying_key().to_string()
        wallet.privateKey = private_key.to_string()
        wallet.publicKey = public_key
        wallet.address = Utils.md5(Utils.sha256(public_key))
        return wallet
    
    @classmethod
    def fromPublic(cls,publicKey:bytes):
        wallet = cls()
        wallet.privateKey = None
        wallet.publicKey = publicKey
        wallet.address = Utils.md5(Utils.sha256(publicKey))
        return wallet
    
    def sign(self,data:bytes) -> bytes:
        private_key = SigningKey.from_string(self.privateKey,NIST256p,hashlib.sha256)
        signature = private_key.sign(data)
        return signature

    def verify_signature(self,signature:bytes,data:bytes):
        public_key = VerifyingKey.from_string(self.publicKey,NIST256p,hashlib.sha256)
        try:
            if public_key.verify(signature,data):
                return True
            else:
                return False
        except:
            return False
    
    def info(self):
        return f"privateKey | {self.privateKey.hex()}\npublicKey  | {self.publicKey.hex()}\naddress    | {self.address.hex()}"
