-- ** Anomaly detection **
-- Compute an anomaly score for each record in the source stream using Random Cut Forest
-- Creates a temporary stream and defines a schema
CREATE OR REPLACE STREAM "TEMP_STREAM" (
   "sensor_id"        VARCHAR,
   "temperature"      DOUBLE,
   "rpm"              DOUBLE,
   "in_service"       BOOLEAN,
   "ANOMALY_SCORE"    DOUBLE);

   -- Creates an output stream and defines a schema
CREATE OR REPLACE STREAM "PROCESS_STREAM" (
   "sensor_id"        VARCHAR,
   "temperature"      DOUBLE,
   "rpm"              DOUBLE,
   "in_service"       BOOLEAN,
   "ANOMALY_SCORE"    DOUBLE);

-- Compute an anomaly score for each record in the source stream
-- using Random Cut Forest
CREATE OR REPLACE PUMP "STREAM_PUMP" AS INSERT INTO "TEMP_STREAM"
SELECT STREAM "sensor_id", "temperature", "rpm", "in_service", "ANOMALY_SCORE" FROM
  TABLE(RANDOM_CUT_FOREST(
    CURSOR(SELECT STREAM * FROM "SOURCE_SQL_STREAM_001")
  )
);
-- Sort records by descending anomaly score, insert into output stream
CREATE OR REPLACE PUMP "PROCESS_PUMP" AS INSERT INTO "PROCESS_STREAM"
SELECT STREAM * FROM "TEMP_STREAM"
WHERE ANOMALY_SCORE > 1.5
ORDER BY FLOOR("TEMP_STREAM".ROWTIME TO SECOND), ANOMALY_SCORE DESC;