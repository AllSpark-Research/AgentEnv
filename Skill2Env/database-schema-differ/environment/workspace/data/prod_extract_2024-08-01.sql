-- =====================================================================
-- Lumen Books — production data extract (sampled) for migration testing
-- Captured: 2024-08-01 02:20 UTC
-- Apply on top of schema/prod_2024-08-01.sql to get a test fixture.
-- Amounts are stored as REAL dollars (pre-v2.3.0 convention).
-- =====================================================================

INSERT INTO customers (id, email, full_name, created_at) VALUES
  (1, 'maya.chen@example.com', 'Maya Chen', '2023-11-02 10:14:55'),
  (2, 'liam.obrien@example.net', 'Liam O''Brien', '2023-12-19 08:02:11'),
  (3, 'sofia.ramirez@example.org', 'Sofía Ramírez', '2024-01-07 15:44:03'),
  (4, 'noah.patel@example.com', 'Noah Patel', '2024-02-14 11:20:37'),
  (5, 'emma.wilson@example.net', 'Emma Wilson', '2024-03-01 09:31:26'),
  (6, 'lucas.meyer@example.org', 'Lucas Meyer', '2024-03-22 18:05:49'),
  (7, 'ava.kim@example.com', 'Ava Kim', '2024-05-09 13:57:12'),
  (8, 'ethan.brown@example.net', 'Ethan Brown', '2024-06-30 07:41:58');

INSERT INTO books (id, isbn, title, author, list_price, published_year, stock_count) VALUES
  (1, '9780132350884', 'Clean Code', 'Robert C. Martin', 39.99, 2008, 14),
  (2, '9780201616224', 'The Pragmatic Programmer', 'Andrew Hunt', 42.50, 1999, 7),
  (3, '9780596007126', 'Head First Design Patterns', 'Eric Freeman', 54.95, 2004, 3),
  (4, '9781491950298', 'Designing Data-Intensive Applications', 'Martin Kleppmann', 59.99, 2017, 9),
  (5, '9780321127426', 'Patterns of Enterprise Application Architecture', 'Martin Fowler', 64.99, NULL, 5),
  (6, '9781617294945', 'Grokking Algorithms', 'Aditya Bhargava', 24.95, 2016, 21),
  (7, '9780262033848', 'Introduction to Algorithms', 'Thomas H. Cormen', 89.95, 2009, 2),
  (8, '9780134685991', 'Effective Java', 'Joshua Bloch', 54.95, 2017, 6),
  (9, '9781449331818', 'Learning SQL', 'Alan Beaulieu', 34.99, 2009, 11),
  (10, '9781951204006', 'Fundamentals of Data Engineering', 'Joe Reis', 59.99, 2022, 4);

INSERT INTO orders (id, customer_id, order_date, status, total) VALUES
  (1, 1, '2024-06-02 10:22:01', 'shipped', 84.98),
  (2, 3, '2024-06-05 19:14:44', 'shipped', 59.99),
  (3, 2, '2024-06-12 08:03:17', 'delivered', 114.94),
  (4, 1, '2024-06-21 16:47:29', 'delivered', 24.95),
  (5, 5, '2024-06-28 12:35:50', 'delivered', 94.94),
  (6, 4, '2024-07-03 09:58:02', 'delivered', 179.90),
  (7, 6, '2024-07-09 21:19:33', 'shipped', 34.99),
  (8, 8, '2024-07-15 14:06:27', 'pending', 129.98),
  (9, 7, '2024-07-19 17:52:41', 'pending', 42.50),
  (10, 2, '2024-07-24 10:31:05', 'shipped', 54.95),
  (11, 5, '2024-07-27 20:44:18', 'pending', 89.95),
  (12, 3, '2024-07-30 13:09:56', 'pending', 69.95);

INSERT INTO order_items (id, order_id, book_id, quantity, unit_price) VALUES
  (1, 1, 1, 1, 39.99),
  (2, 1, 3, 1, 44.99),
  (3, 2, 4, 1, 59.99),
  (4, 3, 2, 1, 42.50),
  (5, 3, 6, 2, 36.22),
  (6, 4, 6, 1, 24.95),
  (7, 5, 4, 1, 59.99),
  (8, 5, 9, 1, 34.95),
  (9, 6, 7, 2, 89.95),
  (10, 7, 9, 1, 34.99),
  (11, 8, 5, 1, 64.99),
  (12, 8, 10, 1, 64.99),
  (13, 9, 2, 1, 42.50),
  (14, 10, 8, 1, 54.95),
  (15, 11, 7, 1, 89.95),
  (16, 12, 1, 1, 39.99),
  (17, 12, 9, 1, 29.96),
  (18, 3, 6, 1, 36.22),
  (19, 6, 3, 1, 0.00),
  (20, 1, 9, 1, 0.00),
  (21, 5, 8, 1, 0.00),
  (22, 8, 6, 1, 0.00);

INSERT INTO legacy_promo_codes (id, code, discount_pct, expires) VALUES
  (1, 'WELCOME10', 10.0, '2024-08-31'),
  (2, 'SPRING15', 15.0, '2024-04-30'),
  (3, 'BDAY20', 20.0, NULL),
  (4, 'LOYAL5', 5.0, '2025-01-01'),
  (5, 'FLASH25', 25.0, '2024-07-01'),
  (6, 'STUDENT12', 12.0, '2024-12-31'),
  (7, 'GIFT8', 8.0, '2024-09-15'),
  (8, 'VIP30', 30.0, NULL),
  (9, 'RETAIL10', 10.0, '2024-11-30'),
  (10, 'NEWSLETTER5', 5.0, NULL),
  (11, 'SUMMER18', 18.0, '2024-08-15'),
  (12, 'CLEARANCE22', 22.0, '2024-06-30'),
  (13, 'REFER9', 9.0, '2024-10-10'),
  (14, 'BUNDLE14', 14.0, '2024-09-01'),
  (15, 'ARCHIVE3', 3.0, NULL);

INSERT INTO temp_dba_scratchpad (note) VALUES
  ('INC-2041: perf baseline q3 captured, keep for comparison'),
  ('INC-2041: plan cache flushed at 02:10'),
  ('INC-2041: follow-up ticket OPS-1201');
