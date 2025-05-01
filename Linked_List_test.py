from database_connector import create_connection
from typing import List


class Node:
    def __init__(self, data = None) -> None:
        self.data = data
        self.next = None

    def __repr__(self) -> str:
        return f'{self.data} -> {self.next}' if self.next else f'{self.data}'


class Linked_List:
    def __init__(self):
        self.head = Node()

    def create_linked_list(self, arr: List[int]) -> None:
        if not arr: return

        cur_node = self.head
        for val in arr:
            new_node = Node(val)
            cur_node.next = new_node
            cur_node = new_node


if __name__ == '__main__':
    nums: List[int] = [2, 3, 4, 5]
    linked_list = Linked_List()
    linked_list.create_linked_list(nums)
    print(linked_list.head.next)