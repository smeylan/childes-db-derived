CREATE USER IF NOT EXISTS 'reader'@'%' IDENTIFIED BY 'childspeech';
DROP DATABASE IF EXISTS childes_db_derived_dev;
CREATE DATABASE childes_db_derived_dev;
GRANT ALL PRIVILEGES ON childes_db_derived_dev.* TO 'root'@'localhost';
GRANT SELECT ON childes_db_derived_dev.* TO 'reader'@'%';
