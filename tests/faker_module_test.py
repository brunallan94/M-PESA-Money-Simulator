from faker import Faker
from faker.config import AVAILABLE_LOCALES
import random
import hashlib

print(AVAILABLE_LOCALES)

# Initialize Faker with the default locale (en_US)
faker = Faker()
Faker.seed(0)  # Seed for Faker
random.seed(0)  # Seed for Python's random module

# List of Kenyan cities
kenyan_cities = [
    "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret",
    "Thika", "Malindi", "Kitale", "Garissa", "Kakamega"
]

for _ in range(10):
    name = faker.name()
    # Generate a Safaricom-like number starting with '2547'
    phone = f"2547{random.randint(10000000, 99999999)}"
    city = random.choice(kenyan_cities)  # Randomly select a Kenyan city
    dob = faker.date_of_birth(minimum_age=18, maximum_age=60)
    gender = random.choice(['male', 'female'])
    pin = f"{random.randint(0, 9999):04d}"  # Generate a 4-digit PIN
    hashed_pin = hashlib.sha256(pin.encode()).hexdigest()  # Hash the PIN
    print(name, phone, gender, dob, city, hashed_pin)
