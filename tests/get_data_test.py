import requests
from typing import List
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


def main() -> None:
    link: str = 'https://randomuser.me/api/?results=10'
    kenyan_towns = load_kenyan_towns()
    n: int = 10  # Number of users to fetch

    # Create database connection
    connection = create_connection()

    try:
        response = requests.get(link)
        response.raise_for_status()
        results = response.json()['results']
    except requests.exceptions.RequestException as e:
        print(f'Error fetching user data: {e}')
        return

    for i, data in enumerate(tqdm(results, desc='Downloading......', ncols=75, disable=False), start=1):
        try:
            full_name: str = f"{data['name']['title']} {data['name']['first']} {data['name']['last']}"
            prefixes = ['2547', '2541', '2540']
            number: str = f"{random.choice(prefixes)}{random.randint(10000000, 99999999)}"
            gender: str = data['gender']
            dob: str = data['dob']['date'][:10]
            age: int = data['dob']['age']
            raw_balance: str = str(data['location']['postcode'])
            balance: str = re.sub(r'[^\d]', '', raw_balance) or '0'
            place: str = random.choice(kenyan_towns)
            pin = int(data['location']['street']['number']) % 10000
            account_created_on = data['registered']['date'][:10]

            user: User = User(full_name, number, gender, dob, age, balance, place, account_created_on, pin)
            user.import_to_sql(connection)

            # Use tqdm.write() for clean output during tqdm progress
            tqdm.write(str(user))
            tqdm.write(f'Hashed PIN: {user.hashed_pin}')
            tqdm.write('_' * 60)

        except Exception as e:
            tqdm.write(f"Error processing user #{i}: {e}")

    connection.close()


if __name__ == '__main__':
    main()
