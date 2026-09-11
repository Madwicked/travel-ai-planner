CREATE DATABASE IF NOT EXISTS travel_ai_planner
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE travel_ai_planner;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS api_cache;
DROP TABLE IF EXISTS trip_places;
DROP TABLE IF EXISTS trip_hotels;
DROP TABLE IF EXISTS trip_transports;
DROP TABLE IF EXISTS trips;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE trips (
  id INT AUTO_INCREMENT PRIMARY KEY,
  origin VARCHAR(255) NOT NULL,
  origin_country VARCHAR(100) NULL,
  origin_latitude DOUBLE NULL,
  origin_longitude DOUBLE NULL,
  destination VARCHAR(255) NOT NULL,
  destination_country VARCHAR(100) NULL,
  destination_currency VARCHAR(3) NULL,
  user_currency VARCHAR(3) NULL,
  destination_latitude DOUBLE NULL,
  destination_longitude DOUBLE NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  travelers INT NOT NULL,
  budget DOUBLE NULL,
  interests TEXT NULL,
  transport_type VARCHAR(50) NULL,
  transport_price DOUBLE NULL,
  transport_duration VARCHAR(50) NULL,
  transport_departure VARCHAR(10) NULL,
  transport_arrival VARCHAR(10) NULL,
  transport_departure_date DATE NULL,
  transport_arrival_date DATE NULL,
  transport_departure_location VARCHAR(255) NULL,
  transport_arrival_location VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE trip_transports (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trip_id INT NOT NULL,
  parent_transport_id INT NULL,
  direction VARCHAR(20) NOT NULL,
  transport_type VARCHAR(50) NOT NULL,
  transport_price DOUBLE NOT NULL,
  currency VARCHAR(3) NOT NULL,
  transport_duration VARCHAR(50) NOT NULL,
  departure_date DATE NOT NULL,
  departure_time VARCHAR(10) NOT NULL,
  departure_location VARCHAR(255) NOT NULL,
  arrival_date DATE NOT NULL,
  arrival_time VARCHAR(10) NOT NULL,
  arrival_location VARCHAR(255) NOT NULL,
  CONSTRAINT fk_trip_transports_trip
    FOREIGN KEY (trip_id) REFERENCES trips(id),
  CONSTRAINT fk_trip_transports_parent
    FOREIGN KEY (parent_transport_id) REFERENCES trip_transports(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE trip_hotels (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trip_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  city VARCHAR(255) NOT NULL,
  address VARCHAR(255) NOT NULL,
  price_per_night DOUBLE NOT NULL,
  nights INT NOT NULL,
  total_price DOUBLE NOT NULL,
  currency VARCHAR(3) NOT NULL,
  check_in DATE NOT NULL,
  check_out DATE NOT NULL,
  CONSTRAINT fk_trip_hotels_trip
    FOREIGN KEY (trip_id) REFERENCES trips(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE trip_places (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trip_id INT NOT NULL,
  external_id VARCHAR(255) NULL,
  source VARCHAR(50) NOT NULL DEFAULT 'mock',
  name VARCHAR(255) NOT NULL,
  city VARCHAR(255) NOT NULL,
  category VARCHAR(100) NOT NULL,
  address VARCHAR(255) NOT NULL,
  latitude DOUBLE NULL,
  longitude DOUBLE NULL,
  rating DOUBLE NULL,
  opening_hours JSON NULL,
  opening_time VARCHAR(10) NOT NULL,
  closing_time VARCHAR(10) NOT NULL,
  visit_duration VARCHAR(20) NULL,
  CONSTRAINT fk_trip_places_trip
    FOREIGN KEY (trip_id) REFERENCES trips(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE api_cache (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trip_id INT NOT NULL,
  cache_type VARCHAR(50) NOT NULL,
  direction VARCHAR(20) NULL,
  data TEXT NOT NULL,
  fetched_at DATETIME NOT NULL,
  INDEX ix_api_cache_trip_id (trip_id),
  CONSTRAINT fk_api_cache_trip
    FOREIGN KEY (trip_id) REFERENCES trips(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
