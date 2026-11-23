-- ============================================================
-- Project: Education & Migration Background in the Netherlands
-- Data:    CBS StatLine table 80122NED
--          Exam candidates and graduates in secondary education
--          by school type and migration background, 2005/06 to 2020/21
-- Author:  Remy Rukundo
-- Tool:    SQLite (DB Browser for SQLite)
-- Table:   exam_results_clean (432 rows)
-- Columns: school_type, background, school_year, candidates, graduates, pass_rate_pct
--
-- Notes on the data
--  * 'All candidates (total)' is the total of ALL candidates, including Dutch background.
--    It is left out of group comparisons so nobody is counted twice.
--  * 'Unknown' has very few candidates (often about 10) and is left out of comparisons.
--  * The 2020/21 figures are provisional (CBS).
--  * The data describe exam candidates, not all pupils, and show differences between
--    groups, not causes.
-- ============================================================


-- Data check: expect 432 rows, 3 school types, 9 backgrounds, 16 school years
SELECT COUNT(*)                    AS total_rows,
       COUNT(DISTINCT school_type) AS school_types,
       COUNT(DISTINCT background)  AS backgrounds,
       COUNT(DISTINCT school_year) AS school_years
FROM exam_results_clean;


-- Question 1: What were the exam results in the latest school year (2020/21)?
SELECT school_type, background, candidates, graduates, pass_rate_pct
FROM exam_results_clean
WHERE school_year = '2020/21'
ORDER BY school_type, background;


-- Question 2: Which groups had the lowest VWO pass rate in 2020/21?
SELECT background, candidates, graduates, pass_rate_pct
FROM exam_results_clean
WHERE school_year = '2020/21'
  AND school_type = 'VWO'
  AND background NOT IN ('All candidates (total)', 'Unknown')
ORDER BY pass_rate_pct ASC;


-- Question 3: How many exam candidates did each group have over all 16 years,
--             and what was their overall pass rate?
SELECT background,
       SUM(candidates) AS total_candidates,
       SUM(graduates)  AS total_graduates,
       ROUND(100.0 * SUM(graduates) / SUM(candidates), 1) AS pass_rate
FROM exam_results_clean
WHERE background NOT IN ('All candidates (total)', 'Unknown')
GROUP BY background
ORDER BY total_candidates DESC;


-- Question 4: What share of each group's candidates were in VWO or HAVO
--             in 2005/06 compared with 2020/21?
SELECT background,
       school_year,
       SUM(candidates) AS total_candidates,
       ROUND(100.0 * SUM(CASE WHEN school_type IN ('VWO', 'HAVO') THEN candidates ELSE 0 END)
             / SUM(candidates), 1) AS pct_vwo_havo
FROM exam_results_clean
WHERE school_year IN ('2005/06', '2020/21')
  AND background NOT IN ('All candidates (total)', 'Unknown')
GROUP BY background, school_year
ORDER BY background, school_year;


-- Question 5: What share of exam candidates were in VWO, HAVO and VMBO each year,
--             for all migration backgrounds combined compared with Dutch background?
SELECT CASE WHEN background = 'Dutch background' THEN 'Dutch background'
            ELSE 'Migration background' END AS group_name,
       school_year,
       SUM(candidates) AS total_candidates,
       ROUND(100.0 * SUM(CASE WHEN school_type = 'VWO'  THEN candidates ELSE 0 END) / SUM(candidates), 1) AS pct_vwo,
       ROUND(100.0 * SUM(CASE WHEN school_type = 'HAVO' THEN candidates ELSE 0 END) / SUM(candidates), 1) AS pct_havo,
       ROUND(100.0 * SUM(CASE WHEN school_type = 'VMBO' THEN candidates ELSE 0 END) / SUM(candidates), 1) AS pct_vmbo
FROM exam_results_clean
WHERE background NOT IN ('All candidates (total)', 'Unknown')
GROUP BY group_name, school_year
ORDER BY group_name, school_year;
