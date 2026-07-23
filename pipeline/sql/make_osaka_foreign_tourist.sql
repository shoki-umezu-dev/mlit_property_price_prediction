CREATE SCHEMA IF NOT EXISTS silver_zone
OPTIONS(location = 'asia-northeast1');

CREATE OR REPLACE TABLE silver_zone.osaka_foreign_tourists AS 
SELECT year, actual_foreign_guests
FROM `raw_zone.osaka_foreign_tourists`
ORDER BY year;