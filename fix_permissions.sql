-- Run this in pgAdmin 4 Query Tool
-- Right-click on your PostgreSQL 16 > Query Tool

-- Connect to the bettafish database first!
-- Make sure you're connected to database: bettafish

-- Grant all privileges on schema public
GRANT ALL ON SCHEMA public TO bettafish1;

-- Grant create privilege
GRANT CREATE ON SCHEMA public TO bettafish1;

-- Grant all privileges on all tables (current and future)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bettafish1;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bettafish1;

-- Make bettafish1 the owner of the schema (optional but recommended)
ALTER SCHEMA public OWNER TO bettafish1;

-- Verify the grants worked
SELECT grantee, privilege_type 
FROM information_schema.role_table_grants 
WHERE grantee = 'bettafish1';
