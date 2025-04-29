import time
import requests
from typing import List, Set
import pprint as pp
import hashlib
import re
import random
import json
from database_connector import create_connection
from tqdm import tqdm
import sys


class User:
    def __init__(self, name, phone_number, gender, dob, age, balance, place_of_birth, account_created_on, pin) -> None:
        self.name = name
        self.phone_number = phone_number
        self.gender = gender
        self.dob = dob
        self.age = age
        self.balance = balance
        self.place_of_birth = place_of_birth
        self.account_created_on = account_created_on
        self.pin = f'{pin:04d}'
        self.hashed_pin = self._hash_pin(self.pin)

    def _hash_pin(self, pin) -> str:
        return hashlib.sha256(str(pin).encode()).hexdigest()

    def __repr__(self) -> str:
        return f'{self.name} | Phone: {self.phone_number} | Balance: KES {int(self.balance):,} | Town: {self.place_of_birth}'

    def import_to_sql(self, connection):
        cursor = connection.cursor()

        try:
            cursor.execute('INSERT INTO users (full_name, phone_number, gender, dob, age, balance, place_of_birth, account_created_on, pin, hashed_pin)'
                           'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                           (self.name, self.phone_number, self.gender, self.dob, self.age, self.balance, self.place_of_birth, self.account_created_on, self.pin, self.hashed_pin))
            connection.commit()

        except Exception as e:
            print(f'Error inserting user {self.name}: {e}')

        finally:
            cursor.close()


def load_kenyan_towns() -> List[str]:
    # Load towns from the json file
    with open('files/kenyan_counties.json', 'r') as f:
        counties = json.load(f)

    # Extract all sub_counties (towns) from each county
    towns = []
    for county in counties:
        towns.extend(county.get('sub_counties', []))

    return towns


def generate_unique_phone(existing_numbers: Set[str]) -> str:
    prefixes: List[str] = ['254110', '254111', '254112', '254113', '254114', '254115', '254740', '254741', '254742', '254743', '254745', '254746', '254748', '254757', '254758', '254759', '254768', '254769']
    # unused_prefixes: List[str] = ['25472', '25471', '25470', '25479']
    # 25470 ranges from 700-709
    # 25471 ranges from 710-719
    # 25472 ranges from 720-729
    # 25479 ranges from 790-799

    while True:
        number: str = f"{random.choice(prefixes)}{random.randint(100_000, 999_999)}"
        if number not in existing_numbers:
            existing_numbers.add(number)
            return number


def process_batch(batch_size: int, batch_num: int, existing_no: Set[str], connection) -> None:
    link: str = f'https://randomuser.me/api/?results={batch_size}'
    kenyan_towns = load_kenyan_towns()

    try:
        response = requests.get(link)
        response.raise_for_status()
        res = response.json()['results']

    except requests.exceptions.RequestException as e:
        print(f'Error fetching user data: {e}')
        return

    for i, data in enumerate(tqdm(res, desc=f'Downloading batch number: {batch_num +1}', leave=False, ncols=75), start=1):
        try:
            full_name: str = f"{data['name']['title']} {data['name']['first']} {data['name']['last']}"  # Name
            number: str = generate_unique_phone(existing_no)  # Phone number
            gender: str = data['gender']  # Gender
            dob: str = data['dob']['date'][:10]  # Date of Birth
            age: int = data['dob']['age']  # Age
            raw_balance: str = str(data['location']['postcode'])
            balance: str = re.sub(r'[^\d]', '', raw_balance) or '0'  # Mpesa Balance
            place: str = random.choice(kenyan_towns)  # Place of Birth
            pin = int(data['location']['street']['number']) % 10000  # Mpesa pin
            account_created_on = data['registered']['date'][:10]  # Date of account Mpesa account creation/registration

            user: User = User(full_name, number, gender, dob, age, balance, place, account_created_on, pin)
            user.import_to_sql(connection)
            # tqdm.write(str(user))
            # tqdm.write(f'Hashed PIN: {user.hashed_pin}')
            # tqdm.write('_' * 60)

        except Exception as e:
            tqdm.write(f'Error processing user: {i} -> {e}')
            continue


def main_get_data():
    """The random user api has a limit of 5000"""
    api_delay: int = 2
    total_users_required: int = 100_000
    batch_size: int = 5_000
    num_batches: int = total_users_required // batch_size
    used_numbers: Set[str] = set()
    connection = create_connection()  # Create database connection

    for batch_num in tqdm(range(num_batches), desc='Overall Progress', ncols=80):
        process_batch(batch_size, batch_num, used_numbers, connection)
        time.sleep(api_delay)

    connection.close()  # Close database connection


if __name__ == '__main__':
    main_get_data()