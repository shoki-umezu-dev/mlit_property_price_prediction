CREATE SCHEMA IF NOT EXISTS silver_zone
OPTIONS(location = 'asia-northeast1');

CREATE OR REPLACE TABLE silver_zone.osaka_pref AS 
WITH int_cast AS (
  SELECT 
  id, 
  CAST(transaction_price AS INT64) AS transaction_price,
  CAST(coverage_ratio AS INT64) AS coverage_ratio,
  CAST(floor_area_ratio AS INT64) AS floor_area_ratio
  FROM `raw_zone.osaka_pref`
), null_int AS (
  SELECT
    id, 
    CAST(NULLIF(area_sqm, '2,000㎡以上') AS INT64) AS area_sqm, 
    CASE WHEN area_sqm = '2,000㎡以上' THEN 1 ELSE 0 END AS area_no_max_limit_flag,
    CAST(SUBSTRING(NULLIF(building_year, '戦前'), 1, 4) AS INT64) AS building_year,
    CASE WHEN building_year = '戦前' THEN 1 ELSE 0 END AS building_before_war_flag,
    CASE WHEN time_to_station LIKE '%～%' THEN 1 ELSE 0 END AS time_range_write_flag,
    CASE WHEN time_to_station = '2H～' THEN 1 ELSE 0 END AS time_no_max_limit_flag,
    CAST(CASE time_to_station 
    WHEN '30分～60分' THEN '45' 
    WHEN '1H～1H30' THEN '75' 
    WHEN '1H30～2H' THEN '105' 
    WHEN '2H～' THEN '135'
    ELSE time_to_station END AS INT64) AS time_to_station,
    CAST(SUBSTRING(transaction_period, 1, 4) AS INT64) AS transaction_year,
    CASE SUBSTRING(transaction_period, 7, 1) 
    WHEN "4" THEN 4 
    WHEN "3" THEN 3 
    WHEN "2" THEN 2 
    ELSE 1 END AS transaction_quarter
  FROM `raw_zone.osaka_pref`
), others AS (
  SELECT 
    id, 
    type, 
    price_info_class, 
    municipality_code, 
    prefecture, 
    municipality, 
    district, 
    nearest_station, 
    layout, 
    structure, 
    use, 
    future_use, 
    city_planning, 
    renovation, 
    transaction_notes
  FROM `raw_zone.osaka_pref`
)
SELECT *
FROM others
JOIN int_cast
USING (id)
JOIN null_int
USING (id);