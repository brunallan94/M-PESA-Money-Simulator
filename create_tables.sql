CREATE DATABASE IF NOT EXISTS mpesa_sim;
USE mpesa_sim;
-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    phone_number VARCHAR(20) UNIQUE,
    gender ENUM('male', 'female') NOT NULL,
    dob DATE,
    age INT,
    balance DECIMAL(10, 2) DEFAULT 0,
    place_of_birth VARCHAR(100),
    account_created_on DATE,
    pin CHAR(4),
    hashed_pin CHAR(64)
);
-- 2. Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2),
    description TEXT,
    date_of_transaction DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
-- Optional: Agents table (for future tree structure)
CREATE TABLE IF NOT EXISTS agents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    region VARCHAR(100)
);
-- Optional: User-Group link (if grouping users later)
CREATE TABLE IF NOT EXISTS user_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    group_name VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Company Revenue table
CREATE TABLE IF NOT EXISTS company_revenue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    transaction_type VARCHAR(50) NOT NULL,
    charge DECIMAL(10, 2),
    amount DECIMAL(10, 2),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);