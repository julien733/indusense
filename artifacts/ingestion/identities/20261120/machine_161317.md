* Source: D:\indusense\datas\machine.sql.txt
* Filsize: 22.41 Ko
* ProcessBeginAt: 16:13:17
* ProcessEndAt: 16:13:17
* Charset: UTF-8
* Rows Number: 130
* Cols Number: 22
* Tables Number: 2

## Tables

| Table | Rows Number | Cols Number |
| --- | ---: | ---: |
| machine | 15 | 11 |
| maintenance | 115 | 11 |

## Column list

| Table | Colname | Infered Type |
| --- | --- | --- |
| machine | machine_code | IDENTITY |
| machine | commissioning_date | DATE |
| machine | max_daily_capacity | NUMERIC |
| machine | max_hourly_capacity_pieces | NUMERIC |
| machine | model | TEXT |
| machine | production_line | TEXT |
| machine | location | TEXT |
| machine | criticality | TEXT |
| machine | is_active | BOOLEAN |
| machine | created_at | DATETIME |
| machine | updated_at | DATETIME |
| maintenance | maintenance_id | IDENTITY |
| maintenance | machine_code | IDENTITY |
| maintenance | maintenance_at | DATETIME |
| maintenance | maintenance_type | TEXT |
| maintenance | action_type | TEXT |
| maintenance | component | TEXT |
| maintenance | description | TEXT |
| maintenance | related_incident_id | IDENTITY |
| maintenance | duration_hours | NUMERIC |
| maintenance | created_at | DATETIME |
| maintenance | updated_at | DATETIME |

## Numeric and temporal statistics

| Table | Col name | Infered Type | Min value | Max value | Mean value | Median value |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| machine | commissioning_date | DATE | 2019-07-23 | 2025-05-25 | N/A | N/A |
| machine | max_daily_capacity | NUMERIC | 750 | 1428 | 1054.866667 | 1027 |
| machine | max_hourly_capacity_pieces | NUMERIC | 47 | 89 | 65.86666667 | 64 |
| machine | created_at | DATETIME | 2026-11-20 15:13:17 | 2026-11-20 15:13:17 | N/A | N/A |
| machine | updated_at | DATETIME | 2026-11-20 15:13:17 | 2026-11-20 15:13:17 | N/A | N/A |
| maintenance | maintenance_at | DATETIME | 2025-06-15 06:00:00+00 | 2026-05-30 22:00:00+00 | N/A | N/A |
| maintenance | duration_hours | NUMERIC | 1.00 | 8.00 | 2.943043478 | 2.64 |
| maintenance | created_at | DATETIME | 2026-11-20 15:13:17 | 2026-11-20 15:13:17 | N/A | N/A |
| maintenance | updated_at | DATETIME | 2026-11-20 15:13:17 | 2026-11-20 15:13:17 | N/A | N/A |
