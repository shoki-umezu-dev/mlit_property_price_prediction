CREATE SCHEMA IF NOT EXISTS silver_zone
OPTIONS(location = 'asia-northeast1');

CREATE OR REPLACE TABLE silver_zone.osaka_foreign_residents AS 
WITH residents_14_24 AS (
SELECT *
FROM `raw_zone.osaka_foreign_residents`
WHERE year != 2025
ORDER BY year
),residents_25 AS (
  SELECT 
  SUBSTRING(municipality, 7) AS municipality,
  foreign_male_counts,
  foreign_female_counts,
  total_counts,
  include_foreign_household_counts,
  year
  FROM `raw_zone.osaka_foreign_residents`
  WHERE year = 2025
)
SELECT *
FROM residents_14_24
UNION ALL
SELECT *
FROM residents_25;