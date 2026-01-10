-- Create schema structure for warehouse.sales_data.fact_orders
-- Run this in SQL Server Management Studio

-- Create warehouse database if it doesn't exist
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'warehouse')
BEGIN
    CREATE DATABASE warehouse;
END
GO

USE warehouse;
GO

-- Create sales_data schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'sales_data')
BEGIN
    EXEC('CREATE SCHEMA sales_data');
END
GO

-- Drop table if it exists (for clean testing)
IF OBJECT_ID('sales_data.fact_orders', 'U') IS NOT NULL
    DROP TABLE sales_data.fact_orders;
GO

-- Create the fact_orders table
CREATE TABLE sales_data.fact_orders (
    order_id INT PRIMARY KEY,
    amount DECIMAL(18, 2) NOT NULL,
    region NVARCHAR(50) NOT NULL
);
GO

-- Insert test data
INSERT INTO sales_data.fact_orders (order_id, amount, region) VALUES
(1, 7500.00, 'US-West'),
(2, 3200.00, 'US-West'),
(3, 8900.00, 'US-East'),
(4, 5500.00, 'US-West'),
(5, 4800.00, 'US-West'),
(6, 12000.00, 'US-West'),
(7, 2100.00, 'EU-North'),
(8, 6200.00, 'US-West'),
(9, 9500.00, 'APAC'),
(10, 5100.00, 'US-West');
GO

-- Verify the data
SELECT * FROM sales_data.fact_orders;
GO

-- Query that matches the Logica HighValueSales predicate:
-- US-West region with amount > 5000
SELECT order_id, amount
FROM sales_data.fact_orders
WHERE region = 'US-West' AND amount > 5000;
GO
