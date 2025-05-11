import threading
from concurrent.futures import ThreadPoolExecutor
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
    def __init__(self, users_to_insert) -> None:
        self.users_to_insert = users_to_insert

    def __repr__(self) -> str:
        name, phone, gender, dob, age, balance, place_of_birth, account_created, pin, hashed_pin = self.users_to_insert
        return f'{name} | Phone: {phone} | Balance: KES {int(balance):,} | Town: {place_of_birth}'

    def import_to_sql(self, connection):
        cursor = connection.cursor()

        try:
            cursor.executemany(''' INSERT INTO users (full_name, phone_number, gender, dob, age, balance, place_of_birth, account_created_on, pin, hashed_pin) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ''', self.users_to_insert)
            connection.commit()

        except Exception as e:
            print(f'Error inserting user: {e}')

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


def fetch_phone_numbers_in_database(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT phone_number FROM users")
    results = {row[0] for row in cursor.fetchall()}
    cursor.close()
    return results


def fetch_with_retry(url: str, retries: int = 3, backoff: int = 5) -> requests.Response:
    headers = {'User-Agent': 'M-PESA Money Simulator/1.0'}

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                wait = backoff * (attempt +1)
                tqdm.write(f"[Retry {attempt +1}] Rate limited. Retrying in {wait} seconds.....")
                time.sleep(wait)

            else:
                tqdm.write(f"HTTP Error: {e}")
                break

        except requests.exceptions.RequestException as e:
            tqdm.write(f"Requests failed: {e}")
            time.sleep(backoff)

    raise RuntimeError('Max retries exceeded for API request.')


def process_batch(batch_size: int, batch_num: int, existing_no: Set[str], lock: threading.Lock, api_delay) -> None:
    link: str = f'https://randomuser.me/api/?results={batch_size}'
    kenyan_towns = load_kenyan_towns()
    connection = create_connection()
    users_to_insert = []

    try:
        response = fetch_with_retry(link)
        res = response.json()['results']

    except requests.exceptions.RequestException as e:
        print(f'Error fetching user data in batch {batch_num +1}: {e}')
        return

    for i, data in enumerate(tqdm(res, desc=f'Downloading batch number: {batch_num +1}', leave=False, ncols=75), start=1):
        try:
            full_name: str = f"{data['name']['title']} {data['name']['first']} {data['name']['last']}"  # Name
            with lock: number: str = generate_unique_phone(existing_no)  # Phone number. The lock ensures no 2 threads assign the same phone number.
            gender: str = data['gender']  # Gender
            dob: str = data['dob']['date'][:10]  # Date of Birth
            age: int = data['dob']['age']  # Age
            raw_balance: str = str(data['location']['postcode'])
            balance: str = re.sub(r'[^\d]', '', raw_balance) or '0'  # Mpesa Balance
            place: str = random.choice(kenyan_towns)  # Place of Birth
            pin = int(data['location']['street']['number']) % 10000  # Mpesa pin
            hashed_pin = hashlib.sha256(str(pin).encode()).hexdigest()
            account_created_on = data['registered']['date'][:10]  # Date of account Mpesa account creation/registration

            users_to_insert.append((full_name, number, gender, dob, age, balance, place, account_created_on, pin, hashed_pin))

        except Exception as e:
            tqdm.write(f'Error processing user: {i} in batch {batch_num +1} -> {e}')
            continue

    if users_to_insert:
        user = User(users_to_insert)
        user.import_to_sql(connection)

    connection.close()
    time.sleep(api_delay)


def main_get_data():
    """The random user api has a limit of 5000"""
    connection = create_connection()
    api_delay: int = random.randint(1, 3)
    total_users_required: int = 100_000
    max_api_batch_size: int = 600
    used_numbers: Set[str] = fetch_phone_numbers_in_database(connection)
    used_numbers_lock = threading.Lock()
    max_concurrent_requests: int = 1
    connection.close()

    batch_sizes: List[int] = []
    remaining = total_users_required
    while remaining > 0:
        batch_sizes.append(min(max_api_batch_size, remaining))
        remaining -= batch_sizes[-1]

    with ThreadPoolExecutor(max_workers=max_concurrent_requests) as executor:
        futures = []

        for batch_num, batch_size in enumerate(batch_sizes):
            futures.append(executor.submit(process_batch, batch_size, batch_num, used_numbers, used_numbers_lock, api_delay))

        for f in tqdm(futures, desc='Overall Progress', ncols=80):
            f.result()


if __name__ == '__main__':
    main_get_data()