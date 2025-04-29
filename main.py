from simulate_transactions import TransactionSimulator
from SQL_database_manager import main_sql
from get_data import main_get_data


def main() -> None:
    pass
    # 1. Create Database
    main_sql()
    # 2. Load data into the database
    main_get_data()
    # 3. Simulate Transactions
    simulator = TransactionSimulator(duration_minutes=30, max_transactions=1000)
    simulator.run_simulation()


if __name__ == '__main__':
    main()