-- =====================================================================
-- Lumen Books — PRODUCTION schema dump
-- Source: prod SQLite database, captured 2024-08-01 02:14 UTC (ops cron)
-- Note:   This is the *actual* state of production, including any objects
--         created outside the normal release process.
-- =====================================================================

PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX idx_customers_email ON customers(email);

CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    isbn TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    list_price REAL NOT NULL,
    published_year INTEGER,
    stock_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_price_perf ON books(list_price);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'pending',
    total REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE INDEX idx_orders_customer ON orders(customer_id);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE INDEX idx_order_items_order ON order_items(order_id);

CREATE TABLE legacy_promo_codes (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL,
    discount_pct REAL NOT NULL,
    expires TEXT
);

CREATE TABLE temp_dba_scratchpad (
    note TEXT
);
