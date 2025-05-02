from database_connector import create_connection
from typing import List


class Node:
    def __init__(self, name: str = None, phone: str = None, balance: float = None, place_of_birth: str = None, transaction_type: str = None,
                 amount: float = None, description: str = None) -> None:
        self.name = name
        self.phone = phone
        self.balance = balance
        self.place_of_birth = place_of_birth
        self.transaction_type = transaction_type
        self.amount = amount
        self.description = description
        self.next = None

    def __repr__(self) -> str:
        return f'{self.name | self.phone | self.balance} -> {self.next}' if self.next else f'{self.name | self.phone | self.balance}'


class LinkedList:
    def __init__(self) -> None:
        self.head = Node()  # Sentinel

    def create_linkedlist(self, data: List[tuple]) -> None:
        if not data: return

        cur_node = self.head
        for name, phone, balance, place_of_birth, transaction_type, amount, description in data:
            new_node = Node(name, phone, balance, place_of_birth, transaction_type, amount, description)
            cur_node.next = new_node
            cur_node = new_node

    def display(self) -> None:
        cur_node = self.head.next

        while cur_node:
            print(f"{cur_node.name} | Phone: {cur_node.phone} | Balance: {cur_node.balance} | transaction Type: {cur_node.transaction_type} | Amount: {cur_node.amount}")
            cur_node = cur_node.next

    def count_data(self) -> None:
        cur_node =self.head.next
        count: int = 0

        while cur_node:
            count += 1
            cur_node = cur_node.next

        print(f"The total amount of users is {count}{'\n'} ")


def main() -> None:
    connection = create_connection()
    cursor = connection.cursor(dictionary=False)

    cursor.execute("SELECT u.full_name, u.phone_number, u.balance, u.place_of_birth, t.transaction_type, t.amount, t.description "
                   "FROM users u "
                   "INNER JOIN transactions t ON u.id = t.user_id "
                   "WHERE balance < 100")
    data = cursor.fetchall()

    linked_list = LinkedList()
    linked_list.create_linkedlist(data)
    linked_list.count_data()
    linked_list.display()


if __name__ == '__main__':
    main()