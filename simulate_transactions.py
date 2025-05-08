import random
import time
from datetime import datetime, timedelta
from database_connector import create_connection
from typing import List, Tuple, Optional

# Transaction types with their probabilities and descriptions
TRANSACTION_TYPES = [
    ('deposit', 0.2, "Cash deposit from agent"),
    ('withdrawal', 0.2, "Cash withdrawal from agent"),
    ('send', 0.3333, "Money sent to another user"),
    ('airtime', 0.13333, "Airtime purchase"),
    ('lipa na mpesa', 0.0667, "Lipa Na MPESA payment"),
    ('paybill', 0.0533, "Paybill payment"),
    ('pochi la biashara', 0.0133, "Pochi La Biashara deposit")
]


class TransactionSimulator:
    def __init__(self, duration_minutes: int = 60, max_transactions: int = 1_000) -> None:
        self.duration_minutes = duration_minutes
        self.max_transactions = max_transactions
        self.connection = create_connection()
        self.cursor = self.connection.cursor(dictionary=True)

    def get_random_users(self, count: int = 2) -> List[dict]:
        """Get random users from the database"""
        self.cursor.execute("SELECT id, full_name, phone_number, balance FROM users ORDER BY RAND() LIMIT %s", (count,))
        return self.cursor.fetchall()

    def get_random_amount(self, user_balance: float) -> float:
        """Generate a random transaction amount based on user balance"""
        max_amount: float = min(float(user_balance) * 0.9, 50_000)
        if max_amount < 10: return 1000
        min_amount: int = 10
        return round(random.uniform(min_amount, max_amount), 2)

    def select_transaction_type(self) -> Tuple[str, str]:
        """Select a transaction type based on weighted probabilities"""
        index = random.choices(range(len(TRANSACTION_TYPES)), weights=[w for _, w, _ in TRANSACTION_TYPES])[0]
        return TRANSACTION_TYPES[index][0], TRANSACTION_TYPES[index][2]

    def calculate_mpesa_charges(self, amount: float, transaction_type: str) -> int:
        send_pochi_till_charges = {'1-49': 0, '50-100': 0, '101-500': 7, '501-1000': 13, '1001-1500': 23,
                                   '1501-2500': 33, '2501-3500': 53, '3501-5000': 57, '5001-7500': 78, '7501-10000': 90,
                                   '10001-15000': 100, '15001-20000': 105, '20001-35000': 108, '35001-50000': 108,
                                   '50001-250000': 108}

        withdraw_charges = {'1-49': 0, '50-100': 11, '101-500': 29, '501-1000': 29, '1001-1500': 29, '1501-2500': 29,
                            '2501-3500': 52, '3501-5000': 69, '5001-7500': 87, '7501-10000': 115, '10001-15000': 167,
                            '15001-20000': 185, '20001-35000': 197, '35001-50000': 278, '50001-250000': 309}

        charged_amount = 0
        charge_map = {}

        if transaction_type in ['paybill', 'pochi la biashara', 'send']: charge_map = send_pochi_till_charges

        elif transaction_type == 'withdrawal': charge_map = withdraw_charges

        else: charged_amount = 0

        for key, val in charge_map.items():
            lower, upper = map(int, key.split('-'))

            if lower <= amount <= upper:
                charged_amount = val
                break

        return charged_amount

    def process_transaction(self, user_id: int, transaction_type: str, amount: float, description: str,
                            recipient_id: Optional[int] = None, user_name: Optional[str] = None,
                            user_phone: Optional['str'] = None) -> bool:
        """Process a transaction and update user balances"""
        try:
            # Start transaction
            if not self.connection.in_transaction:
                self.connection.start_transaction()

            # Get current balance for sender
            self.cursor.execute("SELECT balance FROM users WHERE id = %s FOR UPDATE", (user_id,))
            sender_balance: float = self.cursor.fetchone()['balance']

            # Cut the transaction charge based on the transaction type
            # The reason why charge is equal to amount in airtime is because when one buys airtime the money goes to the company
            if transaction_type == 'airtime': charge: float = amount
            else:
                charge: float = self.calculate_mpesa_charges(amount, transaction_type)
                amount: float = charge + amount

            # Record the transaction to the company revenue database
            self.cursor.execute(
                "INSERT INTO company_revenue (user_id, transaction_type, charge, amount)"
                "VALUES (%s, %s, %s, %s)",
                (user_id, transaction_type, charge, amount))

            # Handle different transaction types
            if transaction_type in ['withdrawal', 'send', 'airtime', 'lipa na mpesa', 'paybill', 'pochi la biashara']:
                if sender_balance < amount:
                    raise ValueError("Insufficient funds")

                new_balance: float = float(sender_balance) - amount
                self.cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))

                # For send transactions, also update recipient balance
                if transaction_type == 'send' and recipient_id:
                    self.cursor.execute("SELECT balance FROM users WHERE id = %s FOR UPDATE", (recipient_id,))
                    recipient_balance = self.cursor.fetchone()['balance']

                    self.cursor.execute("UPDATE users SET balance = %s WHERE id = %s",
                                        (float(recipient_balance) + amount, recipient_id))

                    # Record the receive transaction for recipient
                    self.cursor.execute(
                        "INSERT INTO transactions (user_id, transaction_type, amount, description, date_of_transaction)"
                        "VALUES (%s, 'receive', %s, %s, %s)",
                        (recipient_id, amount, f"Received from {user_name} {user_phone}", datetime.now()))

            elif transaction_type == 'deposit':
                new_balance = float(sender_balance) + amount
                description = f'Money has been {transaction_type} sucessfully'
                self.cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))

            # Record the transaction
            self.cursor.execute(
                "INSERT INTO transactions (user_id, transaction_type, amount, description, date_of_transaction)"
                "VALUES (%s, %s, %s, %s, %s)",
                (user_id, transaction_type, amount, description, datetime.now())
            )

            self.connection.commit()
            return True

        except Exception as e:
            self.connection.rollback()
            print(f"Transaction failed: {e}")
            return False

    def generate_random_transaction(self) -> None:
        """Generate and process a random transaction"""
        # Get 1-2 random users (2 for send transactions)
        transaction_type, description = self.select_transaction_type()

        if transaction_type in ['send', 'pochi la biashara']:
            users = self.get_random_users(2)
            if len(users) < 2: return  # Ensures we get the required 2 users for functionality of the function

            sender, recipient = users
            amount: float = self.get_random_amount(sender['balance'])
            description: str = f"Sent to {recipient['full_name']} {recipient['phone_number']}"

            self.process_transaction(sender['id'], transaction_type, amount, description, recipient['id'],
                                     sender['full_name'], sender['phone_number'])
        else:
            user = self.get_random_users(1)[0]
            amount: float = self.get_random_amount(user['balance'])

            self.process_transaction(user['id'], transaction_type, amount, description)

    def run_simulation(self) -> None:
        """Run the simulation for the specified duration"""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=self.duration_minutes)
        transaction_count = 0

        print(f"Starting transaction simulation for {self.duration_minutes} minutes...")

        while datetime.now() < end_time and transaction_count < self.max_transactions:
            try:
                self.generate_random_transaction()
                transaction_count += 1

                # Random delay between transactions (0.1 to 5 seconds)
                time.sleep(random.uniform(0.1, 5))

                # Print progress every 10 transactions
                if transaction_count % 10 == 0: print(f"Processed {transaction_count} transactions...")

            except Exception as e:
                print(f"Error in simulation: {e}")
                time.sleep(1)  # Wait a bit before retrying

        print(f"Simulation complete. Processed {transaction_count} transactions in {self.duration_minutes} minutes.")

    def __del__(self):
        """Clean up database connections"""
        self.cursor.close()
        self.connection.close()


def transaction_charges():
    send_pochi_till_charges = {'1-49': 0, '50-100': 0, '101-500': 7, '501-1000': 13, '1001-1500': 23, '1501-2500': 33,
                               '2501-3500': 53, '3501-5000': 57, '5001-7500': 78, '7501-10000': 90, '10001-15000': 100,
                               '15001-20000': 105, '20001-35000': 108, '35001-50000': 108, '50001-250000': 108}
    withdraw_charges = {'50-100': 11, '101-500': 29, '501-1000': 29, '1001-1500': 29, '1501-2500': 29, '2501-3500': 52,
                        '3501-5000': 69, '5001-7500': 87, '7501-10000': 115, '10001-15000': 167, '15001-20000': 185,
                        '20001-35000': 197, '35001-50000': 278, '50001-250000': 309}


if __name__ == '__main__':
    simulator = TransactionSimulator(duration_minutes=30, max_transactions=1000)
    simulator.run_simulation()
