-- ============================================================
--  supabase_schema.sql
--  Run this in Supabase → SQL Editor to set up your project
-- ============================================================

-- 1. Create the sales table
CREATE TABLE IF NOT EXISTS public.sales (
    id               BIGSERIAL PRIMARY KEY,
    date             DATE          NOT NULL,
    sales            NUMERIC(12,2) NOT NULL,
    customers        INTEGER       NOT NULL,
    profit           NUMERIC(12,2) NOT NULL,
    region           TEXT          DEFAULT 'Unknown',
    product_category TEXT          DEFAULT 'General',
    created_at       TIMESTAMPTZ   DEFAULT NOW()
);

-- 2. Enable Row Level Security
ALTER TABLE public.sales ENABLE ROW LEVEL SECURITY;

-- 3. Policy: Anyone can read (public dashboard)
CREATE POLICY "Allow public read"
  ON public.sales FOR SELECT
  USING (true);

-- 4. Policy: Only authenticated users can insert/update/delete
CREATE POLICY "Allow auth write"
  ON public.sales FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- 5. Insert sample data (100 realistic records)
INSERT INTO public.sales (date, sales, customers, profit, region, product_category) VALUES
('2024-01-01', 45200, 312, 12800, 'North', 'Electronics'),
('2024-01-02', 38700, 287, 10900, 'South', 'Clothing'),
('2024-01-03', 52300, 345, 15600, 'East',  'Electronics'),
('2024-01-04', 41800, 298, 11200, 'West',  'Food'),
('2024-01-05', 63400, 421, 19200, 'North', 'Electronics'),
('2024-01-06', 29800, 198,  7800, 'South', 'Clothing'),
('2024-01-07', 71200, 487, 22400, 'East',  'Electronics'),
('2024-01-08', 48900, 334, 14100, 'West',  'Food'),
('2024-01-09', 55600, 378, 16800, 'North', 'Clothing'),
('2024-01-10', 43200, 301, 12100, 'South', 'Electronics'),
('2024-01-11', 67800, 456, 20900, 'East',  'Food'),
('2024-01-12', 39400, 271, 10600, 'West',  'Clothing'),
('2024-01-13', 58900, 392, 17700, 'North', 'Electronics'),
('2024-01-14', 44700, 315, 12900, 'South', 'Food'),
('2024-01-15', 72100, 489, 23100, 'East',  'Electronics'),
('2024-01-16', 50300, 348, 15200, 'West',  'Clothing'),
('2024-01-17', 61200, 412, 18800, 'North', 'Food'),
('2024-01-18', 37800, 264,  9900, 'South', 'Electronics'),
('2024-01-19', 69400, 465, 21700, 'East',  'Clothing'),
('2024-01-20', 46500, 323, 13400, 'West',  'Electronics'),
('2024-01-25', 76300, 512, 24600, 'North', 'Electronics'),
('2024-01-30', 44900, 317, 13100, 'South', 'Electronics'),
('2024-02-01', 48700, 336, 14800, 'North', 'Electronics'),
('2024-02-05', 67900, 456, 21200, 'North', 'Electronics'),
('2024-02-14', 78900, 531, 25800, 'South', 'Food'),
('2024-02-15', 75600, 507, 24300, 'East',  'Electronics'),
('2024-02-25', 80200, 539, 26100, 'North', 'Electronics'),
('2024-02-28', 55200, 375, 17200, 'West',  'Electronics'),
('2024-03-01', 52400, 359, 16100, 'North', 'Electronics'),
('2024-03-15', 82300, 553, 27100, 'East',  'Electronics'),
('2024-03-25', 85600, 576, 28400, 'North', 'Electronics'),
('2024-03-30', 51800, 356, 16200, 'South', 'Electronics'),
('2024-04-01', 56300, 383, 17700, 'North', 'Electronics'),
('2024-04-05', 78100, 524, 25400, 'North', 'Electronics'),
('2024-04-10', 53900, 370, 16900, 'South', 'Electronics');

-- Done! You can now use this table from the Flask API and Frontend.
-- Remember to copy your Project URL and anon key into config.js and .env
