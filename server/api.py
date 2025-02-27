from fastapi import APIRouter, HTTPException
import pymysql.cursors
import config as Config
import pigeonium
from time import time
import re
from pydantic import BaseModel
import responseTypes

router = APIRouter()

adminWallet = pigeonium.Wallet.fromPrivate(Config.Network.AdminPrivateKey)
pigeonium.Config.AdminPublicKey = adminWallet.publicKey
pigeonium.Config.NetworkId = Config.Network.NetworkId

def DBConnection():
    cond = Config.MySQL
    connection = pymysql.connect(host=cond.host,port=cond.port,
                                 user=cond.user,password=cond.password,database=cond.database,
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()
    return connection, cursor

def dictFormat(data: dict):
    for dKey in list(data.keys()):
        dValue = data[dKey]
        if type(dValue) == bytes:
            data[dKey] = dValue.hex()
    return data

def strPattern(s:str, pattern:str = r'^[0-9a-zA-Z_]+$'):
    return bool(re.match(pattern, s))

@router.get("/")
async def networkInfo() -> responseTypes.NetworkInfo:
    connection, cursor = DBConnection()
    cursor.execute("SELECT `indexId` FROM `transactions` ORDER BY indexId DESC LIMIT 1")
    latest = cursor.fetchall()
    if latest:
        latestIndexId = latest[0]['indexId']
    else:
        latestIndexId = 0
        genesis = pigeonium.AdminUtil.genesis(Config.Network.BaseCurrencyIssuance,adminWallet)
        genesis.adminConfirm(0, int(time()), adminWallet)
        cursor.execute("INSERT INTO `transactions` (`indexId`,`transactionId`,`timestamp`,`source`,`dest`,`currencyId`,`amount`,`networkId`,`publicKey`,`adminSignature`)"
                       " VALUES (%(indexId)s,%(transactionId)s,%(timestamp)s,%(source)s,%(dest)s,%(currencyId)s,%(amount)s,%(networkId)s,%(publicKey)s,%(adminSignature)s)",
                       genesis.toDict())
        cursor.execute("INSERT INTO `balance` (`address`, `currencyId`, `amount`) VALUES (%s, %s, %s)",(adminWallet.address, genesis.currencyId, genesis.amount))
        cursor.execute("INSERT INTO `currency` (`currencyId`, `name`, `symbol`, `issuer`, `inputData`, `supply`,`issuerSignature`,`publicKey`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                       (genesis.currencyId,Config.Network.BaseCurrencyName,Config.Network.BaseCurrencySymbol,genesis.dest,bytes(),genesis.amount,
                        adminWallet.sign(genesis.currencyId),adminWallet.publicKey))
        connection.commit()
    connection.close()
    swapPoolWallet = pigeonium.Wallet.fromPrivate(Config.Network.SwapWalletPrivateKey)
    return dictFormat(
            {"NetworkName":Config.Network.NetworkName,"PigeoniumVersion":pigeonium.__version__,
            "BaseCurrencyName":Config.Network.BaseCurrencyName,"BaseCurrencySymbol":Config.Network.BaseCurrencySymbol,"GenesisIssuance":Config.Network.BaseCurrencyIssuance,
            "AdminPublicKey":adminWallet.publicKey,"LatestIndexId":latestIndexId,"networkId":Config.Network.NetworkId,"SwapPoolAddress":swapPoolWallet.address})

@router.get("/previousTx")
async def getPreviousTx():
    connection, cursor = DBConnection()
    cursor.execute("SELECT * FROM `transactions` ORDER BY indexId DESC LIMIT 1")
    TxDict = cursor.fetchone()
    tx = pigeonium.Transaction()
    tx.indexId = TxDict['indexId']
    tx.transactionId = TxDict['transactionId']
    tx.timestamp = TxDict['timestamp']
    tx.source = TxDict['source']
    tx.dest = TxDict['dest']
    tx.currencyId = TxDict['currencyId']
    tx.amount = TxDict['amount']
    tx.networkId = TxDict['networkId']
    tx.publicKey = TxDict['publicKey']
    tx.adminSignature = TxDict['adminSignature']
    connection.close()
    return dictFormat(tx.toDict())

@router.get("/balance")
async def getBalance(address: str = "", currencyId: str = "") -> list[responseTypes.Balance]:
    try:
        address = bytes.fromhex(address)
        currencyId = bytes.fromhex(currencyId)
    except ValueError:
        raise HTTPException(400, "'address' or 'currencyId' is invalid format")
    except Exception as e:
        raise e
    connection, cursor = DBConnection()
    sql = "SELECT * FROM `balance`"
    if currencyId and address:
        sql += " WHERE `address` = %s AND `currencyId` = %s"
        args = (address,currencyId)
    elif currencyId:
        sql += " WHERE `currencyId` = %s"
        args = (currencyId,)
    elif address:
        sql += " WHERE `address` = %s"
        args = (address,)
    else:
        raise HTTPException(400, "'address' or 'currencyId' is required")
    cursor.execute(sql,args)
    result = list(cursor.fetchall())
    response = []
    for bal in result:
        response.append({"address": bal['address'].hex(), "currencyId": bal['currencyId'].hex(), "amount": bal['amount']})
    connection.close()
    return response

@router.get("/currency")
async def getCurrency(currencyId: str = None, name: str = None, symbol: str = None):
    while True:
        sql = "SELECT * FROM `currency`"
        args = ()
        try:
            if currencyId:
                currencyId = bytes.fromhex(currencyId)
                sql += " WHERE `currencyId` = %s"
                qrgs = (currencyId,)
                break
            elif name:
                if not strPattern(name):
                    raise HTTPException(400, "'name' is invalid format (0-9a-zA-Z_)")
                sql += " WHERE `name` = %s"
                qrgs = (name,)
                break
            elif symbol:
                if not strPattern(symbol, r'^[a-zA-Z]+$'):
                    raise HTTPException(400, "'symbol' is invalid format (a-zA-Z)")
                sql += " WHERE `symbol` = %s"
                qrgs = (symbol,)
                break
            else:
                raise HTTPException(400, "'currencyId', 'name' or 'symbol' is required")
        except ValueError:
            raise HTTPException(400, "params is invalid format")
        except Exception as e:
            raise e
    
    connection, cursor = DBConnection()

    cursor.execute(sql,args)
    result = list(cursor.fetchall())
    if result:
        result = result[0]
        response = {"currencyId": result['currencyId'].hex(), "name": result['name'], "symbol": result['symbol'],
                    "issuer": result['issuer'].hex(), "inputData": result['inputData'].hex(),
                    "issuerSignature": result['issuerSignature'].hex(), "publicKey": result['publicKey'].hex(),
                    "supply": result['supply']}
    else:
        response = {}
    connection.close()
    return response

@router.get("/currencies")
async def getCurrencies(sortBy:str = "id", sortOrder:str = "ASC"):
    sql = "SELECT * FROM `currency`"
    if not sortOrder in ["ASC", "DESC"]:
        raise HTTPException(400, "invalid param (sortOrder)")
    if sortBy == "id":
        sql += f" ORDER BY `currencyId` {sortOrder}"
    elif sortBy == "name":
        sql += f" ORDER BY `name` {sortOrder}"
    elif sortBy == "suplly":
        sql += f" ORDER BY `supply` {sortOrder}"
    else:
        raise HTTPException(400, "invalid param (sortBy)")
    
    connection, cursor = DBConnection()
    sql += " LIMIT %s"
    cursor.execute(sql,(Config.Server.currenciesResponseLimit,))
    results = list(cursor.fetchall())
    response = []

    for cu in results:
        response.append({"currencyId": cu['currencyId'].hex(), "name": cu['name'], "symbol": cu['symbol'],
                         "issuer": cu['issuer'].hex(), "inputData": cu['inputData'].hex(),
                         "issuerSignature": cu['issuerSignature'].hex(), "publicKey": cu['publicKey'].hex(),
                         "supply": cu['supply']})
    connection.close()
    return response

@router.get("/transaction")
async def getTransaction(transactionId: str = None, indexId: int = None) -> responseTypes.Transaction:
    try:
        if transactionId:
            transactionId = bytes.fromhex(transactionId)
            colm = "transactionId"
            args = (transactionId,)
        elif type(indexId) == int:
            colm = "indexId"
            args = (indexId,)
        else:
            raise HTTPException(400, "'transactionId' or 'indexId' is required")
    except ValueError:
        raise HTTPException(400, "invalid format")
    except Exception as e:
        raise e
    
    connection, cursor = DBConnection()

    cursor.execute(f"SELECT * FROM `transactions` WHERE `{colm}` = %s",args)
    result = list(cursor.fetchall())
    if result:
        response = dictFormat(result[0])
    else:
        response = {}
    connection.close()
    return response

@router.get("/transactions")
async def getTransactions(indexIdFrom:int = None, currencyId:str = "", address:str = "", source:str = "", dest:str = "", volume:int = 0) -> list[responseTypes.Transaction]:
    try:
        currencyId = bytes.fromhex(currencyId)
        address = bytes.fromhex(address)
        source = bytes.fromhex(source)
        dest = bytes.fromhex(dest)
    except ValueError:
        raise HTTPException(400, "params are invalid format")
    except Exception as e:
        raise e
    
    connection, cursor = DBConnection()

    sql = "SELECT * FROM `transactions`"
    args = []
    sqlChanged = False

    if not indexIdFrom == None:
        if sqlChanged:
            sql += " AND `indexId` >= %s"
        else:
            sql += " WHERE `indexId` >= %s"
            sqlChanged = True
        args.append(indexIdFrom)
    
    if currencyId:
        if sqlChanged:
            sql += " AND `currencyId` = %s"
        else:
            sql += " WHERE `currencyId` = %s"
            sqlChanged = True
        args.append(currencyId)
    
    if address:
        if sqlChanged:
            sql += " AND (`source` = %s OR `dest` = %s)"
        else:
            sql += " WHERE (`source` = %s OR `dest` = %s)"
            sqlChanged = True
        args.append(address)
        args.append(address)
    
    if source:
        if sqlChanged:
            sql += " AND `source` = %s"
        else:
            sql += " WHERE `source` = %s"
            sqlChanged = True
        args.append(source)
    
    if dest:
        if sqlChanged:
            sql += " AND `dest` = %s"
        else:
            sql += " WHERE `dest` = %s"
            sqlChanged = True
        args.append(dest)
    
    if volume > 0:
        if sqlChanged:
            sql += " AND `amount` >= %s"
        else:
            sql += " WHERE `amount` = %s"
            sqlChanged = True
        args.append(volume)
    
    sql += " LIMIT %s"
    args.append(Config.Server.txResponseLimit)
    cursor.execute(sql,tuple(args))
    result = list(cursor.fetchall())
    txs = []
    if result:
        for tx in result:
            txs.append(dictFormat(tx))

    connection.close()
    return txs

@router.get("/swap/{currencyId}")
async def getSwapInfo(currencyId:str):
    try:
        currencyId = bytes.fromhex(currencyId)
    except ValueError:
        raise HTTPException(400, "'currencyId' is invalid format")
    except Exception as e:
        raise e
    
    connection, cursor = DBConnection()

    cursor.execute("SELECT reserveBaseCurrency, reservePairCurrency, swapFee FROM liquidity_pools WHERE pairCurrency = %s",(currencyId,))
    poolInfo = list(cursor.fetchall())
    cursor.execute("SELECT swapType, inputAmount, outputAmount, timestamp FROM swap_history WHERE pairCurrency = %s LIMIT 10",(currencyId,))
    swapHistory = list(cursor.fetchall())
    cursor.close()
    connection.close()

    if not poolInfo:
        raise HTTPException(400, "pool does not exist")

    response = {"reserveBaseCurrency":poolInfo[0]['reserveBaseCurrency'],
                "reservePairCurrency":poolInfo[0]['reservePairCurrency'],
                "swapFee":poolInfo[0]['swapFee'],
                "history":swapHistory}

    return response

@router.get("/swaps")
async def getSwapInfo():
    connection, cursor = DBConnection()
    pools = {}

    cursor.execute("SELECT pairCurrency, reserveBaseCurrency, reservePairCurrency, swapFee FROM liquidity_pools ORDER BY pairCurrency ASC")
    results = list(cursor.fetchall())
    cursor.close()
    connection.close()

    for pool in results:
        pools[pool['pairCurrency'].hex()] = dictFormat(pool)

    return pools

class transactionPost(BaseModel):
    transactionId:str
    dest:str
    currencyId:str
    amount:int
    publicKey:str

@router.post("/transaction")
async def postTransaction(postData: transactionPost) -> responseTypes.Transaction:
    try:
        sourceWallet = pigeonium.Wallet.fromPublic(bytes.fromhex(postData.publicKey))
        
        transactionId = bytes.fromhex(postData.transactionId)
        source = sourceWallet.address
        dest = bytes.fromhex(postData.dest)
        currencyId = bytes.fromhex(postData.currencyId)
        amount = postData.amount
        publicKey = sourceWallet.publicKey

        if amount > 0xffffffffffffffff or amount < 1:
            raise HTTPException(400, "'amount' is out of range (1 - 256^8-1)")
    except ValueError:
        raise HTTPException(400, "params are invalid format")
    except Exception as e:
        raise e
    
    if source == dest:
        raise HTTPException(400, "cannot be sent to yourself")
    
    connection, cursor = DBConnection()
    cursor.execute("SELECT `indexId` FROM `transactions` ORDER BY indexId DESC LIMIT 1")
    latest = cursor.fetchall()
    latestIndexId = int(latest[0]['indexId'])

    tx = pigeonium.Transaction()
    tx.transactionId = transactionId
    tx.source = source
    tx.dest = dest
    tx.currencyId = currencyId
    tx.amount = amount
    tx.networkId = Config.Network.NetworkId
    tx.publicKey = publicKey

    txCheck, _ = tx.verify()
    if txCheck == False:
        connection.close()
        raise HTTPException(400, "invalid transaction")
    
    cursor.execute("SELECT `amount` FROM `balance` WHERE `address` = %s AND `currencyId` = %s AND `amount` >= %s",(tx.source,tx.currencyId,tx.amount))
    if not cursor.fetchall():
        connection.close()
        raise HTTPException(400, "insufficient balance")

    tx.adminConfirm(latestIndexId + 1, int(time()), adminWallet)

    cursor.execute("UPDATE `balance` SET `amount` = `amount` - %s WHERE `address` = %s AND `currencyId` = %s", (tx.amount,tx.source,tx.currencyId))
    cursor.execute("INSERT INTO `balance` (address, currencyId, amount) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE amount = amount + VALUES(amount)",
                   (tx.dest,tx.currencyId,tx.amount))
    
    if tx.dest == bytes(16):
        cursor.execute("UPDATE `currency` SET `supply` = `supply` - %s WHERE `currencyId` = %s", (tx.amount,tx.currencyId))

    cursor.execute("INSERT INTO `transactions` (`indexId`,`transactionId`,`timestamp`,`source`,`dest`,`currencyId`,`amount`,`networkId`,`publicKey`,`adminSignature`)"
                   " VALUES (%(indexId)s,%(transactionId)s,%(timestamp)s,%(source)s,%(dest)s,%(currencyId)s,%(amount)s,%(networkId)s,%(publicKey)s,%(adminSignature)s)",
                   tx.toDict())
    
    cursor.execute("DELETE FROM `balance` WHERE amount = 0")
    
    connection.commit()
    connection.close()

    return dictFormat(tx.toDict())

class IssuancePost(BaseModel):
    currencyId:str
    name:str
    symbol:str
    inputData:str
    amount:int
    issuerSignature:str
    publicKey:str
    senderPublicKey:str
    senderSignature:str

@router.post("/issuance")
async def postIssuanceTransaction(IssuanceData: IssuancePost) -> responseTypes.Transaction:
    try:
        senderWallet = pigeonium.Wallet.fromPublic(bytes.fromhex(IssuanceData.senderPublicKey))
        if not senderWallet.address in Config.Network.superiorAddress:
            raise HTTPException(403, "sender's address is not present in 'superiorAddress'")
        senderSignature = bytes.fromhex(IssuanceData.senderSignature)
        issuerWallet = pigeonium.Wallet.fromPublic(bytes.fromhex(IssuanceData.publicKey))
        currencyId = bytes.fromhex(IssuanceData.currencyId)
        issuerSignature = bytes.fromhex(IssuanceData.issuerSignature)
        inputData = bytes.fromhex(IssuanceData.inputData)
        if not strPattern(IssuanceData.name):
            raise HTTPException(400, "'name' is invalid format (0-9a-zA-Z_)")
        if not strPattern(IssuanceData.symbol, r'^[a-zA-Z]+$'):
            raise HTTPException(400, "'symbol' is invalid format (a-zA-Z)")
        amount = int(IssuanceData.amount)
        if amount > 0xffffffffffffffff or amount < 1:
            raise HTTPException(400, "'amount' is out of range (1 - 256^8-1)")
    except ValueError:
        raise HTTPException(400, "params are invalid format")
    except Exception as e:
        raise e
    
    newCurrency = pigeonium.Currency()
    newCurrency.currencyId = currencyId
    newCurrency.name,newCurrency.symbol = IssuanceData.name, IssuanceData.symbol
    newCurrency.inputData,newCurrency.issuer = inputData, issuerWallet.address
    newCurrency.publicKey = issuerWallet.publicKey
    newCurrency.issuerSignature = issuerSignature

    if not newCurrency.verify():
        raise HTTPException(400, "invalid currency")
    
    if not senderWallet.verifySignature(currencyId,senderSignature):
        raise HTTPException(400, "invalid 'senderSignature'")
    
    connection, cursor = DBConnection()

    cursor.execute("INSERT `currency` (`currencyId`, `name`, `symbol`, `inputData`, `issuer`, `supply`, `issuerSignature`, `publicKey`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                   "ON DUPLICATE KEY UPDATE supply = supply + VALUES(supply)",
                   (newCurrency.currencyId, newCurrency.name, newCurrency.symbol, newCurrency.inputData, newCurrency.issuer, amount,
                    newCurrency.issuerSignature, newCurrency.publicKey))

    cursor.execute("SELECT `indexId` FROM `transactions` ORDER BY indexId DESC LIMIT 1")
    TxDict = cursor.fetchall()[0]
    previousTxIndex = int(TxDict['indexId'])

    tx = pigeonium.AdminUtil.issuanceTx(newCurrency,amount,adminWallet)
    
    txCheck, _ = tx.verify()
    if txCheck == False:
        connection.close()
        raise HTTPException(400, "invalid transaction")
    
    tx.adminConfirm(previousTxIndex+1, int(time()), adminWallet)

    cursor.execute("INSERT INTO `balance` (address, currencyId, amount) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE amount = amount + VALUES(amount)",
                   (tx.dest,tx.currencyId,tx.amount))

    cursor.execute("INSERT INTO `transactions` (`indexId`,`transactionId`,`timestamp`,`source`,`dest`,`currencyId`,`amount`,`networkId`,`publicKey`,`adminSignature`)"
                   " VALUES (%(indexId)s,%(transactionId)s,%(timestamp)s,%(source)s,%(dest)s,%(currencyId)s,%(amount)s,%(networkId)s,%(publicKey)s,%(adminSignature)s)",
                   tx.toDict())
    
    cursor.execute("DELETE FROM `balance` WHERE amount = 0")
    
    connection.commit()
    connection.close()

    return dictFormat(tx.toDict())

class swapTransactionPost(BaseModel):
    transactionId:str
    amount:int
    publicKey:str

@router.post("/swap/buy/{pairCurrencyId}")
async def postSwapBuy(pairCurrencyId:str,postData:swapTransactionPost) -> responseTypes.Transaction:
    try:
        swapPoolWallet = pigeonium.Wallet.fromPrivate(Config.Network.SwapWalletPrivateKey)
        sourceWallet = pigeonium.Wallet.fromPublic(bytes.fromhex(postData.publicKey))
        
        pairCuId = bytes.fromhex(pairCurrencyId)
        transactionId = bytes.fromhex(postData.transactionId)
        source = sourceWallet.address
        dest = swapPoolWallet.address
        amount = postData.amount
        publicKey = sourceWallet.publicKey

        if amount > 0xffffffffffffffff or amount < 1:
            raise HTTPException(400, "'amount' is out of range (1 - 256^8-1)")
    except ValueError:
        raise HTTPException(400, "params are invalid format")
    except Exception as e:
        raise e
    
    connection, cursor = DBConnection()
    
    cursor.execute("SELECT reserveBaseCurrency FROM liquidity_pools WHERE pairCurrency = %s",(pairCuId,))
    results = list(cursor.fetchall())

    if not results:
        connection.close()
        raise HTTPException(400, "pool does not exist")
    
    cursor.execute("SELECT `indexId`, `transactionId` FROM `transactions` ORDER BY indexId DESC LIMIT 1")
    latest = cursor.fetchall()
    latestIndexId = int(latest[0]['indexId'])

    tx = pigeonium.Transaction()
    tx.transactionId = transactionId
    tx.source = source
    tx.dest = dest
    tx.currencyId = bytes(16)
    tx.amount = amount
    tx.networkId = Config.Network.NetworkId
    tx.publicKey = publicKey

    txCheck, _ = tx.verify()
    if txCheck == False:
        connection.close()
        raise HTTPException(400, "invalid transaction")
    cursor.execute("SELECT `amount` FROM `balance` WHERE `address` = %s AND `currencyId` = %s AND `amount` >= %s",(tx.source,tx.currencyId,tx.amount))
    if not cursor.fetchall():
        connection.close()
        raise HTTPException(400, "insufficient balance")

    tx.adminConfirm(latestIndexId + 1, int(time()), adminWallet)

    cursor.execute("UPDATE `balance` SET `amount` = `amount` - %s WHERE `address` = %s AND `currencyId` = %s", (tx.amount,tx.source,tx.currencyId))
    cursor.execute("INSERT INTO `balance` (address, currencyId, amount) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE amount = amount + VALUES(amount)",
                   (tx.dest,tx.currencyId,tx.amount))
    
    if tx.dest == bytes(16):
        cursor.execute("UPDATE `currency` SET `supply` = `supply` - %s WHERE `currencyId` = %s", (tx.amount,tx.currencyId))

    cursor.execute("INSERT INTO `transactions` (`indexId`,`transactionId`,`timestamp`,`source`,`dest`,`currencyId`,`amount`,`networkId`,`publicKey`,`adminSignature`)"
                   " VALUES (%(indexId)s,%(transactionId)s,%(timestamp)s,%(source)s,%(dest)s,%(currencyId)s,%(amount)s,%(networkId)s,%(publicKey)s,%(adminSignature)s)",
                   tx.toDict())
    
    cursor.execute("SET @output_amount = 0;")
    cursor.execute("CALL swap_currency(%s, %s, %s, @output_amount)",('buy', pairCuId, tx.amount))
    cursor.execute("SELECT @output_amount;")

    output_amount = int(cursor.fetchall()[0]['@output_amount'])
    
    swapTx = pigeonium.Transaction.create(swapPoolWallet, source, pairCuId, output_amount)
    swapTx.adminConfirm(tx.indexId + 1, int(time()), adminWallet)
    
    cursor.execute("SELECT `amount` FROM `balance` WHERE `address` = %s AND `currencyId` = %s AND `amount` >= %s",(swapTx.source,swapTx.currencyId,swapTx.amount))
    if not cursor.fetchall():
        connection.close()
        raise HTTPException(400, "insufficient pool balance")

    cursor.execute("UPDATE `balance` SET `amount` = `amount` - %s WHERE `address` = %s AND `currencyId` = %s", (swapTx.amount,swapTx.source,swapTx.currencyId))
    cursor.execute("INSERT INTO `balance` (address, currencyId, amount) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE amount = amount + VALUES(amount)",
                   (swapTx.dest,swapTx.currencyId,swapTx.amount))

    cursor.execute("INSERT INTO `transactions` (`indexId`,`transactionId`,`timestamp`,`source`,`dest`,`currencyId`,`amount`,`networkId`,`publicKey`,`adminSignature`)"
                   " VALUES (%(indexId)s,%(transactionId)s,%(timestamp)s,%(source)s,%(dest)s,%(currencyId)s,%(amount)s,%(networkId)s,%(publicKey)s,%(adminSignature)s)",
                   swapTx.toDict())
    
    cursor.execute("DELETE FROM `balance` WHERE amount = 0")
    
    connection.commit()
    connection.close()

    return dictFormat(swapTx.toDict())

@router.post("/swap/sell/{pairCurrencyId}")
async def postSwapSell(pairCurrencyId:str,postData:swapTransactionPost) -> responseTypes.Transaction:
    try:
        swapPoolWallet = pigeonium.Wallet.fromPrivate(Config.Network.SwapWalletPrivateKey)
        sourceWallet = pigeonium.Wallet.fromPublic(bytes.fromhex(postData.publicKey))
        
        pairCuId = bytes.fromhex(pairCurrencyId)
        transactionId = bytes.fromhex(postData.transactionId)
        source = sourceWallet.address
        dest = swapPoolWallet.address
        amount = postData.amount
        publicKey = sourceWallet.publicKey

        if amount > 0xffffffffffffffff or amount < 1:
            raise HTTPException(400, "'amount' is out of range (1 - 256^8-1)")
    except ValueError:
        raise HTTPException(400, "params are invalid format")
    except Exception as e:
        raise e
    
    connection, cursor = DBConnection()
    
    cursor.execute("SELECT reserveBaseCurrency FROM liquidity_pools WHERE pairCurrency = %s",(pairCuId,))
    results = list(cursor.fetchall())

    if not results:
        connection.close()
        raise HTTPException(400, "pool does not exist")
    
    cursor.execute("SELECT `indexId`, `transactionId` FROM `transactions` ORDER BY indexId DESC LIMIT 1")
    latest = cursor.fetchall()
    latestIndexId = int(latest[0]['indexId'])

    tx = pigeonium.Transaction()
    tx.transactionId = transactionId
    tx.source = source
    tx.dest = dest
    tx.currencyId = pairCuId
    tx.amount = amount
    tx.networkId = Config.Network.NetworkId
    tx.publicKey = publicKey

    txCheck, _ = tx.verify()
    if txCheck == False:
        connection.close()
        raise HTTPException(400, "invalid transaction")
    
    cursor.execute("SELECT `amount` FROM `balance` WHERE `address` = %s AND `currencyId` = %s AND `amount` >= %s",(tx.source,tx.currencyId,tx.amount))
    if not cursor.fetchall():
        connection.close()
        raise HTTPException(400, "insufficient balance")

    tx.adminConfirm(latestIndexId + 1, int(time()), adminWallet)

    cursor.execute("UPDATE `balance` SET `amount` = `amount` - %s WHERE `address` = %s AND `currencyId` = %s", (tx.amount,tx.source,tx.currencyId))
    cursor.execute("INSERT INTO `balance` (address, currencyId, amount) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE amount = amount + VALUES(amount)",
                   (tx.dest,tx.currencyId,tx.amount))
    
    cursor.execute("INSERT INTO `transactions` (`indexId`,`transactionId`,`timestamp`,`source`,`dest`,`currencyId`,`amount`,`networkId`,`publicKey`,`adminSignature`)"
                   " VALUES (%(indexId)s,%(transactionId)s,%(timestamp)s,%(source)s,%(dest)s,%(currencyId)s,%(amount)s,%(networkId)s,%(publicKey)s,%(adminSignature)s)",
                   tx.toDict())
    
    cursor.execute("SET @output_amount = 0;")
    cursor.execute("CALL swap_currency(%s, %s, %s, @output_amount)",('sell', pairCuId, tx.amount))
    cursor.execute("SELECT @output_amount;")

    output_amount = int(cursor.fetchall()[0]['@output_amount'])
    
    swapTx = pigeonium.Transaction.create(swapPoolWallet, source, bytes(16), output_amount)
    swapTx.adminConfirm(tx.indexId + 1, int(time()), adminWallet)
    
    cursor.execute("SELECT `amount` FROM `balance` WHERE `address` = %s AND `currencyId` = %s AND `amount` >= %s",(swapTx.source,swapTx.currencyId,swapTx.amount))
    if not cursor.fetchall():
        connection.close()
        raise HTTPException(400, "insufficient pool balance")

    cursor.execute("UPDATE `balance` SET `amount` = `amount` - %s WHERE `address` = %s AND `currencyId` = %s", (swapTx.amount,swapTx.source,swapTx.currencyId))
    cursor.execute("INSERT INTO `balance` (address, currencyId, amount) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE amount = amount + VALUES(amount)",
                   (swapTx.dest,swapTx.currencyId,swapTx.amount))
    
    if swapTx.dest == bytes(16):
        cursor.execute("UPDATE `currency` SET `supply` = `supply` - %s WHERE `currencyId` = %s", (swapTx.amount,swapTx.currencyId))

    cursor.execute("INSERT INTO `transactions` (`indexId`,`transactionId`,`timestamp`,`source`,`dest`,`currencyId`,`amount`,`networkId`,`publicKey`,`adminSignature`)"
                   " VALUES (%(indexId)s,%(transactionId)s,%(timestamp)s,%(source)s,%(dest)s,%(currencyId)s,%(amount)s,%(networkId)s,%(publicKey)s,%(adminSignature)s)",
                   swapTx.toDict())
    
    cursor.execute("DELETE FROM `balance` WHERE amount = 0")
    
    connection.commit()
    connection.close()

    return dictFormat(swapTx.toDict())


class SwapConfigsPost(BaseModel):
    reserveBaseCurrency:int
    reservePairCurrency:int
    swapFee:int
    senderSignature:str
    senderPublicKey:str

@router.post("/swap/set/{pairCurrencyId}")
async def postIssuanceTransaction(pairCurrencyId:str,SwapConfigs:SwapConfigsPost):
    try:
        senderWallet = pigeonium.Wallet.fromPublic(bytes.fromhex(SwapConfigs.senderPublicKey))
        if not senderWallet.address in Config.Network.superiorAddress:
            raise HTTPException(403, "sender's address is not present in 'superiorAddress'")
        senderSignature = bytes.fromhex(SwapConfigs.senderSignature)
        poolPairCurrencyId = bytes.fromhex(pairCurrencyId)
    except ValueError:
        raise HTTPException(400, "params are invalid format")
    except Exception as e:
        raise e
    
    reserveBaseCurrency = SwapConfigs.reserveBaseCurrency
    reservePairCurrency = SwapConfigs.reservePairCurrency
    swapFee = SwapConfigs.swapFee

    setData = poolPairCurrencyId + reserveBaseCurrency.to_bytes(8,'big') + reservePairCurrency.to_bytes(8,'big') + swapFee.to_bytes(8,'big')

    if not senderWallet.verifySignature(setData,senderSignature):
        raise HTTPException(400, "invalid 'senderSignature'")
    
    connection, cursor = DBConnection()

    cursor.execute("INSERT `liquidity_pools` (`pairCurrency`, `reserveBaseCurrency`, `reservePairCurrency`, `swapFee`) VALUES (%s, %s, %s, %s) "
                   "ON DUPLICATE KEY UPDATE reserveBaseCurrency = VALUES(reserveBaseCurrency), reservePairCurrency = VALUES(reservePairCurrency), swapFee = VALUES(swapFee)",
                   (poolPairCurrencyId,reserveBaseCurrency,reservePairCurrency,swapFee))
    
    connection.commit()
    connection.close()

    response = {"reserveBaseCurrency":str(reserveBaseCurrency),
                "reservePairCurrency":str(reservePairCurrency),
                "swapFee":str(swapFee)}

    return response
