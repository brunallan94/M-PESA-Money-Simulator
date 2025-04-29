from datetime import datetime
from database_connector import create_connection


class Transaction:
    def __init__(self, amount: int, type_: str, date: str = None, description: str = ''):
        self.amount = amount
        self.type = type_  # E.g Deposit, Withdrawal, Send, Recieve, Pochi-la-biashara, lipa-na-mpesa
        self.date = date if date else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.description = description

    def __repr__(self):
        return f'{self.date} | {self.type.title()}: KES {self.amount} | {self.description}'


class TransactionNode:
    def __init__(self, transaction: Transaction):
        self.transaction = transaction
        self.next = None


class TransactionLinkedList:
    def __init__(self):
        self.head = None

    def add_transaction(self, transaction: Transaction):
        node = TransactionNode(transaction)
        if not self.head:
            self.head = node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = node

    def display_transactions(self):
        current = self.head
        while current:
            print(current.transaction)
            current = current.next
