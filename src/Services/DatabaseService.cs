using System;
using System.Collections.Generic;
using System.Data;
using Microsoft.Data.Sqlite;
using Dapper;
using AlmanzilSouriPos.Models;

namespace AlmanzilSouriPos.Services
{
    public class DatabaseService
    {
        private readonly string _connectionString;

        public DatabaseService(string dbPath = "pos_local.db")
        {
            _connectionString = $"Data Source={dbPath}";
            InitializeDatabase();
        }

        public IDbConnection GetConnection() => new SqliteConnection(_connectionString);

        private void InitializeDatabase()
        {
            using var conn = GetConnection();
            conn.Open();

            // 1. Products & Multi-Unit Barcodes Table
            conn.Execute(@"
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    category_id TEXT,
                    name TEXT NOT NULL,
                    unit_type TEXT DEFAULT 'pcs',
                    has_multi_unit INTEGER DEFAULT 0,
                    piece_barcode TEXT,
                    carton_barcode TEXT,
                    units_per_carton INTEGER DEFAULT 1,
                    piece_price REAL DEFAULT 0.0,
                    piece_cost REAL DEFAULT 0.0,
                    carton_price REAL DEFAULT 0.0,
                    carton_cost REAL DEFAULT 0.0,
                    min_stock_alert REAL DEFAULT 5.0,
                    stock_qty REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1
                );");

            // 2. Customers Table (with Phone Lookup & Address)
            conn.Execute(@"
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT UNIQUE,
                    address TEXT,
                    points INTEGER DEFAULT 0,
                    balance REAL DEFAULT 0.0
                );");

            // 3. Invoices Table
            conn.Execute(@"
                CREATE TABLE IF NOT EXISTS invoices (
                    id TEXT PRIMARY KEY,
                    invoice_number TEXT UNIQUE NOT NULL,
                    customer_id TEXT,
                    customer_name TEXT,
                    customer_phone TEXT,
                    delivery_address TEXT,
                    sale_type TEXT DEFAULT 'in_store',
                    payment_method TEXT DEFAULT 'cash',
                    subtotal REAL DEFAULT 0.0,
                    tax REAL DEFAULT 0.0,
                    discount REAL DEFAULT 0.0,
                    delivery_charge REAL DEFAULT 0.0,
                    net_total REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'completed',
                    is_synced INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );");

            // 4. Invoice Items Table
            conn.Execute(@"
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id TEXT PRIMARY KEY,
                    invoice_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT,
                    unit_sold TEXT DEFAULT 'piece',
                    units_per_carton INTEGER DEFAULT 1,
                    quantity REAL DEFAULT 1.0,
                    unit_price REAL DEFAULT 0.0,
                    total_price REAL DEFAULT 0.0,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                );");

            // 5. Suppliers & Ledger Tables
            conn.Execute(@"
                CREATE TABLE IF NOT EXISTS suppliers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    company TEXT,
                    phone TEXT,
                    address TEXT,
                    current_balance REAL DEFAULT 0.0
                );
                CREATE TABLE IF NOT EXISTS supplier_transactions (
                    id TEXT PRIMARY KEY,
                    supplier_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL DEFAULT 0.0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );");

            // 6. Employees & Payroll Tables
            conn.Execute(@"
                CREATE TABLE IF NOT EXISTS employees (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT DEFAULT 'cashier',
                    phone TEXT,
                    base_salary REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS hr_records (
                    id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL DEFAULT 0.0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );");

            // 7. Expenses Table (Separating Operating Expenses vs Partner Withdrawals)
            conn.Execute(@"
                CREATE TABLE IF NOT EXISTS expenses (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    amount REAL DEFAULT 0.0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );");

            // 8. Settings Table
            conn.Execute(@"
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );");
        }
    }
}
