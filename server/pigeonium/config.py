class Config:
    AdminPublicKey: bytes = bytes(32)
    ServerUrl: str = "http://localhost:14510/"
    maxInputData: int = 2**24-1
