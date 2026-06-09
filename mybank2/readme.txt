
-> TO CREATE DATABSE <-

DROP DATABASE IF EXISTS mybank;
CREATE DATABASE mybank;
USE mybank;

-- ADMIN TABLE
CREATE TABLE admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(50) UNIQUE,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(50) NOT NULL
);

INSERT INTO admin(email, username, password)
VALUES ('admin@gmail.com', 'admin', 'admin123');

-- CUSTOMERS TABLE
CREATE TABLE customers (
    accno BIGINT PRIMARY KEY,
    name VARCHAR(50),
    mobile BIGINT,
    email VARCHAR(50),
    password VARCHAR(50),
    balance DOUBLE
);

-- TRANSACTIONS TABLE

   CREATE TABLE transactions (
    tid INT AUTO_INCREMENT PRIMARY KEY,
    accno BIGINT,
    type VARCHAR(30),
    amount DOUBLE,
    balance DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (accno) REFERENCES customers(accno) ON DELETE CASCADE
);

-- TEST DATA
INSERT INTO customers VALUES
(1001, 'Praveen', 9876543210, 'praveen@gmail.com', 'pass123', 5000);

INSERT INTO transactions (accno, type, amount, balance)
VALUES (1001, 'deposit', 1000, 6000);

-- CHECK
SELECT * FROM admin;
SELECT * FROM customers;
SELECT * FROM transactions;
SHOW TABLES;
DESC admin;