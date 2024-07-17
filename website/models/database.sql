-- Create the database
CREATE DATABASE IF NOT EXISTS hospital_auth;

use hospital_auth;

CREATE TABLE
    users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        session_id VARCHAR(255) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

use hospital_auth;

CREATE TABLE
    doctors (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        phone_number VARCHAR(20),
        field VARCHAR(100) NOT NULL, -- Added field column
        password VARCHAR(255) NOT NULL,
        gender ENUM ('male', 'female') NOT NULL, -- Added gender column as ENUM
        session_id VARCHAR(255) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

USE hospital_auth;

CREATE TABLE
    bookings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(15) NOT NULL,
        email VARCHAR(100) NOT NULL,
        illness VARCHAR(255) NOT NULL,
        date DATE NOT NULL,
        time TIME NOT NULL,
        area VARCHAR(100) NOT NULL,
        city VARCHAR(100) NOT NULL,
        state VARCHAR(100) NOT NULL,
        post_code VARCHAR(20) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending' NOT NULL,
        doctor VARCHAR(100) DEFAULT NULL, -- Added column for doctor with default value NULL
        FOREIGN KEY (session_id) REFERENCES users (id) -- Assuming you have a 'users' table
    );

use hospital_auth;
CREATE TABLE updates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    doctor_name VARCHAR(255) NOT NULL,
    notes TEXT,
    bill VARCHAR(50),
    phone VARCHAR(50),
    notes_path VARCHAR(255), -- Adjust the length as needed for your file paths
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

USE hospital_auth;
CREATE TABLE feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    message TEXT NOT NULL
);


-- approve_booking route changed
-- line 636