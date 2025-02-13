import requests

class Config:
    AdminPublicKey: bytes = bytes(32)
    SwapPoolAddress: bytes = bytes(16)
    ServerUrl: str = "http://localhost:14513/"
    MaxInputData: int = 2**24-1
    NetworkId: int = 0

    @staticmethod
    def getFromServer(ServerUrl:str):
        Config.ServerUrl = ServerUrl
        response = requests.get(Config.ServerUrl)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.text)
            raise e
        except Exception as e:
            raise e
        response = response.json()
        Config.AdminPublicKey = bytes.fromhex(response['AdminPublicKey'])
        Config.SwapPoolAddress = bytes.fromhex(response['SwapPoolAddress'])
