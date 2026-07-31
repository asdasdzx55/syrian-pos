import sqlite3
import os
import uuid
import datetime

class LocalDatabase:
    def __init__(self, db_path="pos_local.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def close(self):
        pass

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Categories Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Products Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    category_id TEXT,
                    sub_category TEXT,
                    name TEXT NOT NULL,
                    unit_type TEXT DEFAULT 'pcs',
                    has_multi_unit INTEGER DEFAULT 0,
                    scale_code TEXT,
                    piece_barcode TEXT,
                    carton_barcode TEXT,
                    extra_barcode TEXT,
                    units_per_carton INTEGER DEFAULT 1,
                    piece_price REAL DEFAULT 0.0,
                    piece_cost REAL DEFAULT 0.0,
                    carton_price REAL DEFAULT 0.0,
                    carton_cost REAL DEFAULT 0.0,
                    min_stock_alert REAL DEFAULT 5.0,
                    low_weight_warning_grams REAL DEFAULT 1000.0,
                    image_path TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Ensure columns exist if table was created previously
            try: cursor.execute("ALTER TABLE products ADD COLUMN sub_category TEXT")
            except sqlite3.OperationalError: pass

            try: cursor.execute("ALTER TABLE products ADD COLUMN extra_barcode TEXT")
            except sqlite3.OperationalError: pass

            try: cursor.execute("ALTER TABLE products ADD COLUMN scale_code TEXT")
            except sqlite3.OperationalError: pass

            # Local Stock Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock (
                    product_id TEXT PRIMARY KEY,
                    quantity_pieces REAL DEFAULT 0.0
                )
            """)

            # Customers Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT UNIQUE,
                    address TEXT,
                    points INTEGER DEFAULT 0,
                    balance REAL DEFAULT 0.0
                )
            """)

            # Invoices Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id TEXT PRIMARY KEY,
                    invoice_number TEXT UNIQUE NOT NULL,
                    customer_id TEXT,
                    customer_name TEXT,
                    customer_phone TEXT,
                    delivery_address TEXT,
                    cashier_id TEXT,
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
                )
            """)

            # Invoice Items Table
            cursor.execute("""
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
                )
            """)

            # Suppliers Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    company TEXT,
                    phone TEXT,
                    address TEXT,
                    current_balance REAL DEFAULT 0.0
                )
            """)

            # Supplier Transactions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supplier_transactions (
                    id TEXT PRIMARY KEY,
                    supplier_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Employees & Payroll Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT DEFAULT 'cashier',
                    phone TEXT,
                    base_salary REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # HR Records
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hr_records (
                    id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL DEFAULT 0.0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Expenses Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    amount REAL DEFAULT 0.0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()
            self.seed_default_data_if_empty()

    def seed_default_data_if_empty(self):
        with self.get_connection() as conn:
            cnt_supp = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
            if cnt_supp == 0:
                default_supps = [
                    ("supp-1", "شركة الشام للأجبان والزيوت", "مستورد أجبان وزيوت", "01277695799", "دمشق / القاهرة", 0.0),
                    ("supp-2", "مطاحن ومحمصة الخيرات الشامية", "بن ومكسرات", "01099887766", "القاهرة - مصر", 0.0),
                    ("supp-3", "مصنع حلويات الشام والبرازق", "حلويات وضيافات", "01122334455", "الجيزة - مصر", 0.0)
                ]
                for s in default_supps:
                    conn.execute("INSERT INTO suppliers (id, name, company, phone, address, current_balance) VALUES (?, ?, ?, ?, ?, ?)", s)

            cnt_emp = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
            if cnt_emp == 0:
                default_emps = [
                    ("emp-1", "أحمد الشامي", "كاشير المحل", "01277695799", 7500.0),
                    ("emp-2", "محمود السوري", "مسؤول المخزن وتوريد", "01011223344", 8000.0),
                    ("emp-3", "سامر البائع", "مساعد مبيعات", "01144556677", 6000.0)
                ]
                for e in default_emps:
                    conn.execute("INSERT INTO employees (id, name, role, phone, base_salary) VALUES (?, ?, ?, ?, ?)", e)

            conn.commit()

    def get_customer_by_phone(self, phone):
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM customers WHERE phone = ?", (phone.strip(),)).fetchone()
            return dict(row) if row else None

    def save_customer(self, name, phone, address=""):
        cust_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO customers (id, name, phone, address) VALUES (?, ?, ?, ?)",
                (cust_id, name, phone, address)
            )
            conn.commit()
            return cust_id

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    def get_setting(self, key, default=None):
        with self.get_connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def get_suppliers(self):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM suppliers ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]

    def save_supplier(self, name, company="", phone="", address="", initial_balance=0.0):
        supp_id = "supp-" + str(uuid.uuid4())[:8]
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO suppliers (id, name, company, phone, address, current_balance) VALUES (?, ?, ?, ?, ?, ?)",
                (supp_id, name, company, phone, address, float(initial_balance))
            )
            conn.commit()
            return supp_id

    def update_supplier_balance(self, supplier_id, delta_amount):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE suppliers SET current_balance = current_balance + ? WHERE id = ?",
                (float(delta_amount), supplier_id)
            )
            conn.commit()

    def record_supplier_payment(self, supplier_id, amount, notes=""):
        tx_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO supplier_transactions (id, supplier_id, type, amount, notes) VALUES (?, ?, 'payment', ?, ?)",
                (tx_id, supplier_id, float(amount), notes)
            )
            conn.execute(
                "UPDATE suppliers SET current_balance = current_balance - ? WHERE id = ?",
                (float(amount), supplier_id)
            )
            conn.commit()

    def get_employees(self):
        with self.get_connection() as conn:
            emps = [dict(r) for r in conn.execute("SELECT * FROM employees WHERE is_active = 1 ORDER BY name ASC").fetchall()]
            for e in emps:
                adv = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM hr_records WHERE employee_id = ? AND type = 'advance'", (e["id"],)).fetchone()[0]
                bon = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM hr_records WHERE employee_id = ? AND type = 'bonus'", (e["id"],)).fetchone()[0]
                pen = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM hr_records WHERE employee_id = ? AND type = 'penalty'", (e["id"],)).fetchone()[0]

                e["total_advances"] = adv
                e["total_bonuses"] = bon
                e["total_penalties"] = pen
                e["net_salary_due"] = max(0.0, e["base_salary"] + bon - adv - pen)
            return emps

    def save_employee(self, name, role="cashier", phone="", base_salary=0.0):
        emp_id = "emp-" + str(uuid.uuid4())[:8]
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO employees (id, name, role, phone, base_salary) VALUES (?, ?, ?, ?, ?)",
                (emp_id, name, role, phone, float(base_salary))
            )
            conn.commit()
            return emp_id

    def update_employee_salary(self, employee_id, new_salary):
        with self.get_connection() as conn:
            conn.execute("UPDATE employees SET base_salary = ? WHERE id = ?", (float(new_salary), employee_id))
            conn.commit()

    def add_hr_record(self, employee_id, record_type, amount, description=""):
        rec_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO hr_records (id, employee_id, type, amount, description) VALUES (?, ?, ?, ?, ?)",
                (rec_id, employee_id, record_type, float(amount), description)
            )
            conn.commit()

    def reset_monthly_payroll(self):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM hr_records")
            conn.commit()

    def sync_catalog(self, categories, products, stocks, customers):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for cat in categories:
                cursor.execute(
                    "INSERT OR REPLACE INTO categories (id, name, description, is_active) VALUES (?, ?, ?, ?)",
                    (cat["id"], cat["name"], cat.get("description"), cat.get("is_active", 1))
                )
            for prod in products:
                cursor.execute("""
                    INSERT OR REPLACE INTO products (
                        id, category_id, sub_category, name, unit_type, has_multi_unit, scale_code,
                        piece_barcode, carton_barcode, extra_barcode, units_per_carton,
                        piece_price, piece_cost, carton_price, carton_cost,
                        min_stock_alert, low_weight_warning_grams, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prod["id"], prod.get("category_id"), prod.get("sub_category"), prod["name"], prod.get("unit_type", "pcs"),
                    1 if prod.get("has_multi_unit") else 0, prod.get("scale_code"),
                    prod.get("piece_barcode"), prod.get("carton_barcode"), prod.get("extra_barcode"), prod.get("units_per_carton", 1),
                    float(prod.get("piece_price", 0)), float(prod.get("piece_cost", 0)),
                    float(prod.get("carton_price", 0)) if prod.get("carton_price") else 0.0,
                    float(prod.get("carton_cost", 0)) if prod.get("carton_cost") else 0.0,
                    float(prod.get("min_stock_alert", 5)), float(prod.get("low_weight_warning_grams", 1000)),
                    1 if prod.get("is_active", True) else 0
                ))
            for st in stocks:
                cursor.execute(
                    "INSERT OR REPLACE INTO stock (product_id, quantity_pieces) VALUES (?, ?)",
                    (st["product_id"], float(st["quantity_pieces"]))
                )
            for cust in customers:
                cursor.execute(
                    "INSERT OR REPLACE INTO customers (id, name, phone, address, points, balance) VALUES (?, ?, ?, ?, ?, ?)",
                    (cust["id"], cust["name"], cust.get("phone"), cust.get("address", ""), cust.get("points", 0), float(cust.get("balance", 0)))
                )
            conn.commit()

    def get_products(self, query=""):
        with self.get_connection() as conn:
            if query:
                q = f"%{query}%"
                rows = conn.execute("""
                    SELECT p.*, COALESCE(s.quantity_pieces, 0) as stock_qty 
                    FROM products p 
                    LEFT JOIN stock s ON p.id = s.product_id 
                    WHERE p.id LIKE ? OR p.name LIKE ? OR p.scale_code LIKE ? OR p.piece_barcode LIKE ? OR p.carton_barcode LIKE ? OR p.extra_barcode LIKE ? OR p.category_id LIKE ? OR p.sub_category LIKE ?
                """, (q, q, q, q, q, q, q, q)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT p.*, COALESCE(s.quantity_pieces, 0) as stock_qty 
                    FROM products p 
                    LEFT JOIN stock s ON p.id = s.product_id
                """).fetchall()
            return [dict(r) for r in rows]

    def get_product_by_scale_code(self, scale_code):
        code_str = str(scale_code).strip()
        code_unpadded = code_str.lstrip("0")
        with self.get_connection() as conn:
            row = conn.execute("""
                SELECT p.*, COALESCE(s.quantity_pieces, 0) as stock_qty 
                FROM products p 
                LEFT JOIN stock s ON p.id = s.product_id 
                WHERE p.scale_code = ? OR p.scale_code = ? OR p.piece_barcode = ? OR p.extra_barcode = ?
            """, (code_str, code_unpadded, code_str, code_str)).fetchone()
            return dict(row) if row else None

    def save_invoice(self, invoice_data, items):
        inv_id = invoice_data.get("id") or str(uuid.uuid4())
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (
                    id, invoice_number, customer_id, customer_name, customer_phone, delivery_address,
                    cashier_id, sale_type, payment_method, subtotal, tax, discount, delivery_charge, net_total, status, is_synced, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
            """, (
                inv_id, invoice_data["invoice_number"], invoice_data.get("customer_id"),
                invoice_data.get("customer_name", "عميل نقدي"), invoice_data.get("customer_phone", ""),
                invoice_data.get("delivery_address", ""), invoice_data.get("cashier_id"),
                invoice_data.get("sale_type", "in_store"), invoice_data.get("payment_method", "cash"),
                invoice_data["subtotal"], invoice_data.get("tax", 0.0), invoice_data.get("discount", 0.0),
                invoice_data.get("delivery_charge", 0.0), invoice_data["net_total"],
                invoice_data.get("status", "completed")
            ))

            for item in items:
                item_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO invoice_items (
                        id, invoice_id, product_id, product_name, unit_sold, units_per_carton, quantity, unit_price, total_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_id, inv_id, item["product_id"], item["name"],
                    item["unit_sold"], item.get("units_per_carton", 1), item["quantity"], item["unit_price"], item["total_price"]
                ))

                deduct_qty = item["quantity"]
                if item["unit_sold"] == "carton":
                    deduct_qty *= item.get("units_per_carton", 1)
                
                cursor.execute(
                    "UPDATE stock SET quantity_pieces = quantity_pieces - ? WHERE product_id = ?",
                    (deduct_qty, item["product_id"])
                )

            conn.commit()
            return inv_id

    def save_purchase_invoice(self, supplier_id, invoice_number, is_credit, total_amount, items):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for item in items:
                prod_id = item["product_id"]
                add_qty = float(item["piece_qty"]) + float(item.get("bonus_qty", 0))
                cursor.execute("""
                    INSERT OR REPLACE INTO stock (product_id, quantity_pieces)
                    VALUES (?, COALESCE((SELECT quantity_pieces FROM stock WHERE product_id = ?), 0) + ?)
                """, (prod_id, prod_id, add_qty))

                if item.get("buy_price") and float(item["buy_price"]) > 0:
                    cursor.execute("UPDATE products SET piece_cost = ? WHERE id = ?", (float(item["buy_price"]), prod_id))

            if is_credit and supplier_id:
                cursor.execute(
                    "UPDATE suppliers SET current_balance = current_balance + ? WHERE id = ?",
                    (float(total_amount), supplier_id)
                )
                cursor.execute(
                    "INSERT INTO supplier_transactions (id, supplier_id, type, amount, notes) VALUES (?, ?, 'purchase_credit', ?, ?)",
                    (str(uuid.uuid4()), supplier_id, float(total_amount), f"فاتورة توريد آجل رقم #{invoice_number}")
                )

            conn.commit()

    def save_expense(self, exp_type, amount, description=""):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO expenses (id, type, amount, description) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), exp_type, float(amount), description)
            )
            conn.commit()

    def get_expenses(self):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM expenses ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def get_net_profit_summary(self):
        with self.get_connection() as conn:
            sales = conn.execute("SELECT COALESCE(SUM(net_total), 0) FROM invoices WHERE status = 'completed'").fetchone()[0]
            
            cogs = conn.execute("""
                SELECT COALESCE(SUM(
                    CASE WHEN ii.unit_sold = 'carton' THEN ii.quantity * ii.units_per_carton * p.piece_cost
                         ELSE ii.quantity * p.piece_cost END
                ), 0)
                FROM invoice_items ii
                JOIN products p ON ii.product_id = p.id
                JOIN invoices i ON ii.invoice_id = i.id
                WHERE i.status = 'completed'
            """).fetchone()[0]

            expenses = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE type = 'operating'").fetchone()[0]
            salaries = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM hr_records").fetchone()[0]
            withdrawals = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE type = 'partner_withdrawal'").fetchone()[0]

            net_profit = sales - (cogs + expenses + salaries)
            return {
                "total_sales": sales,
                "cogs": cogs,
                "operating_expenses": expenses,
                "salaries": salaries,
                "partner_withdrawals": withdrawals,
                "net_profit": net_profit
            }

    def get_pending_invoices(self):
        with self.get_connection() as conn:
            invoices = [dict(r) for r in conn.execute("SELECT * FROM invoices WHERE is_synced = 0").fetchall()]
            for inv in invoices:
                items = [dict(r) for r in conn.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (inv["id"],)).fetchall()]
                inv["items"] = items
            return invoices

    def mark_invoices_synced(self, invoice_ids):
        with self.get_connection() as conn:
            for inv_id in invoice_ids:
                conn.execute("UPDATE invoices SET is_synced = 1 WHERE id = ?", (inv_id,))
            conn.commit()
