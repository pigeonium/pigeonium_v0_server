from .wallet import Wallet
from .transaction import Transaction
from .currency import Currency
from .config import Config

class AdminUtil:
    @staticmethod
    def confirmTx(transaction:Transaction, indexId:int, txTimestamp:int, adminWallet:Wallet):
        signature = adminWallet.sign(indexId.to_bytes(8, 'big') + transaction.transactionId + txTimestamp.to_bytes(8, 'big'))
        transaction.indexId = indexId
        transaction.timestamp = txTimestamp
        transaction.adminSignature = signature
        return transaction
    
    @staticmethod
    def issuanceTx(currency:Currency, amount:int, adminWallet:Wallet):
        tx = Transaction()
        tx.transactionId = adminWallet.sign(currency.issuer + currency.currencyId + amount.to_bytes(8, 'big') + Config.NetworkId.to_bytes(8, 'big'))
        tx.source = bytes(16)
        tx.dest = currency.issuer
        tx.currencyId = currency.currencyId
        tx.amount = amount
        tx.networkId = Config.NetworkId
        tx.publicKey = adminWallet.publicKey
        return tx
    
    @staticmethod
    def genesis(amount:int, adminWallet:Wallet):
        tx = Transaction()
        tx.transactionId = adminWallet.sign(adminWallet.address + bytes(16) + amount.to_bytes(8, 'big') + Config.NetworkId.to_bytes(8, 'big'))
        tx.source = bytes(16)
        tx.dest = adminWallet.address
        tx.currencyId = bytes(16)
        tx.amount = amount
        tx.networkId = Config.NetworkId
        tx.publicKey = adminWallet.publicKey
        return tx
