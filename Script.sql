USE travel_ai_planner;
SELECT * FROM trips;
SELECT COUNT(*) FROM trips;

ALTER TABLE trips
ADD COLUMN origin VARCHAR(255) NULL;

UPDATE trips
SET origin = 'Belgrade, Serbia'
WHERE origin IS NULL;

ALTER TABLE trips
MODIFY COLUMN origin VARCHAR(255) NOT NULL;

SELECT id, origin, destination, start_date, end_date
FROM trips;

ALTER TABLE trips
ADD COLUMN transport_type VARCHAR(50) NULL;

ALTER TABLE trips
ADD COLUMN transport_price DECIMAL(10,2) NULL;

ALTER TABLE trips
ADD COLUMN transport_duration VARCHAR(50) NULL;

ALTER TABLE trips
ADD COLUMN transport_arrival VARCHAR(10) NULL;

ALTER TABLE trips
ADD COLUMN transport_departure VARCHAR(10) NULL;

SELECT
    id,
    origin,
    destination,
    transport_type,
    transport_price,
    transport_duration,
    transport_departure,
    transport_arrival
FROM trips;

SELECT
    id,
    origin,
    destination,
    transport_type,
    transport_price,
    transport_duration,
    transport_departure,
    transport_arrival
FROM trips
WHERE id = 7;

ALTER TABLE trips
ADD COLUMN transport_departure_date DATE NULL;

ALTER TABLE trips
ADD COLUMN transport_arrival_date DATE NULL;

ALTER TABLE trips
ADD COLUMN transport_departure_location VARCHAR(255) NULL;

ALTER TABLE trips
ADD COLUMN transport_arrival_location VARCHAR(255) NULL;

CREATE TABLE trip_transports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trip_id INT NOT NULL,
    direction VARCHAR(20) NOT NULL,
    transport_type VARCHAR(50) NOT NULL,
    transport_price DECIMAL(10,2) NOT NULL,
    transport_duration VARCHAR(50) NOT NULL,
    departure_date DATE NOT NULL,
    departure_time VARCHAR(10) NOT NULL,
    departure_location VARCHAR(255) NOT NULL,
    arrival_date DATE NOT NULL,
    arrival_time VARCHAR(10) NOT NULL,
    arrival_location VARCHAR(255) NOT NULL,
    FOREIGN KEY (trip_id) REFERENCES trips(id)
);

SELECT *
FROM trip_transports
WHERE trip_id = 7
ORDER BY id;

CREATE TABLE trip_hotels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trip_id INT NOT NULL,

    name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,

    price_per_night DECIMAL(10,2) NOT NULL,
    nights INT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,

    check_in DATE NOT NULL,
    check_out DATE NOT NULL,

    FOREIGN KEY (trip_id) REFERENCES trips(id)
);

CREATE TABLE trip_places (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trip_id INT NOT NULL,

    name VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,

    opening_time VARCHAR(10) NOT NULL,
    closing_time VARCHAR(10) NOT NULL,

    visit_duration VARCHAR(20) NOT NULL,

    FOREIGN KEY (trip_id) REFERENCES trips(id)
);

ALTER TABLE trip_places
ADD COLUMN external_id VARCHAR(255) NULL,
ADD COLUMN source VARCHAR(50) NOT NULL DEFAULT 'mock',
ADD COLUMN latitude DECIMAL(10,7) NULL,
ADD COLUMN longitude DECIMAL(10,7) NULL,
ADD COLUMN rating DECIMAL(3,2) NULL,
ADD COLUMN opening_hours JSON NULL;
);

DESCRIBE trip_places;

UPDATE trip_places
SET opening_hours = JSON_OBJECT(
    'monday', JSON_ARRAY(opening_time, closing_time),
    'tuesday', JSON_ARRAY(opening_time, closing_time),
    'wednesday', JSON_ARRAY(opening_time, closing_time),
    'thursday', JSON_ARRAY(opening_time, closing_time),
    'friday', JSON_ARRAY(opening_time, closing_time),
    'saturday', JSON_ARRAY(opening_time, closing_time),
    'sunday', JSON_ARRAY(opening_time, closing_time)
);

SELECT
    id,
    name,
    opening_time,
    closing_time,
    opening_hours
FROM trip_places;

SELECT *
FROM trip_places
WHERE trip_id = 7;

SELECT
    id,
    trip_id,
    name,
    source,
    external_id,
    latitude,
    longitude,
    rating,
    opening_hours,
    visit_duration
FROM trip_places
WHERE trip_id = 7
ORDER BY id;

SELECT
    id,
    trip_id,
    name,
    external_id
FROM trip_places
WHERE trip_id = 7
ORDER BY id;