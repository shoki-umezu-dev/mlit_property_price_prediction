CREATE SCHEMA IF NOT EXISTS silver_zone
OPTIONS(location = 'asia-northeast1');

CREATE OR REPLACE TABLE silver_zone.osaka_accommodations AS 
WITH accom_area AS (
  SELECT
  industry, 
  SUBSTRING(facility_location, 4, 3) AS pref,
  SUBSTRING(facility_location, 7, STRPOS(facility_location, "区")-6) AS municipality
  FROM `raw_zone.osaka_accommodations`
)
SELECT 
municipality, 
COUNT(1) AS facility_count
FROM accom_area
GROUP BY municipality;