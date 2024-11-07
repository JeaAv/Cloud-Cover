CREATE DATABASE IF NOT EXISTS cloud_data;
USE cloud_data;

-- Table to store location data
CREATE TABLE IF NOT EXISTS locations (
    location_id INT PRIMARY KEY AUTO_INCREMENT,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    elevation DECIMAL(5, 2),
    location_name VARCHAR(100)
);

-- Table to store unit data
CREATE TABLE IF NOT EXISTS units (
    unit_id INT PRIMARY KEY AUTO_INCREMENT,
    time_unit VARCHAR(50),
    cloud_cover_unit VARCHAR(50),
    visibility_unit VARCHAR(50)
);

-- Table to store current cloud cover data
CREATE TABLE IF NOT EXISTS current_cloud_cover (
    current_cloud_id INT PRIMARY KEY AUTO_INCREMENT,
    location_id INT NOT NULL,
    time DATETIME NOT NULL,
    cloud_cover_total DECIMAL(5, 2) NOT NULL,
    cloud_cover_low DECIMAL(5, 2),
    cloud_cover_mid DECIMAL(5, 2),
    cloud_cover_high DECIMAL(5, 2),
    visibility DECIMAL(5, 2),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);

-- Table to store hourly cloud cover data
CREATE TABLE IF NOT EXISTS hourly_cloud_cover (
    hourly_cloud_id INT PRIMARY KEY AUTO_INCREMENT,
    location_id INT NOT NULL,
    time DATETIME NOT NULL,
    cloud_cover_total DECIMAL(5, 2) NOT NULL,
    cloud_cover_low DECIMAL(5, 2),
    cloud_cover_mid DECIMAL(5, 2),
    cloud_cover_high DECIMAL(5, 2),
    visibility DECIMAL(5, 2),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);

-- Table to store user data (username and hashed password)
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, password) VALUES ('Jea', '777');

