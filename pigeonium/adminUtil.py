from .wallet import Wallet
from .transaction import Transaction
from .currency import Currency

class AdminUtil:
    @staticmethod
    def confirmTx(transaction:Transaction, indexId:int, txTimestamp:int, adminWallet:Wallet):
        signature = adminWallet.sign(indexId.to_bytes(8, 'big') + transaction.transactionId + txTimestamp.to_bytes(8, 'big') + transaction.previous)
        transaction.indexId = indexId
        transaction.timestamp = txTimestamp
        transaction.adminSignature = signature
        return transaction
    
    @staticmethod
    def issuanceTx(currency:Currency, amount:int, previous:bytes, adminWallet:Wallet):
        tx = Transaction()
        tx.transactionId = adminWallet.sign(currency.issuer + currency.currencyId + amount.to_bytes(8, 'big') + previous)
        tx.source = bytes(16)
        tx.dest = currency.issuer
        tx.currencyId = currency.currencyId
        tx.amount = amount
        tx.previous = previous
        tx.publicKey = adminWallet.publicKey
        return tx
    
    @staticmethod
    def genesis(amount:int, adminWallet:Wallet):
        tx = Transaction()
        tx.transactionId = adminWallet.sign(adminWallet.address + bytes(16) + amount.to_bytes(8, 'big') + bytes(64))
        tx.source = bytes(16)
        tx.dest = adminWallet.address
        tx.currencyId = bytes(16)
        tx.amount = amount
        tx.previous = bytes(64)
        tx.publicKey = adminWallet.publicKey
        return tx
