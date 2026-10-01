-- Ensure judge0 database exists alongside default zero1_db
SELECT 'CREATE DATABASE judge0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'judge0')\gexec
