import requests
import json
import datetime
import time

class ApiClient:
    def __init__(self, base_url="https://supermarkrt.almagd555.com"):
        self.base_url = base_url.rstrip("/")
        self.fallback_url = "http://127.0.0.1:8000"
        self.api_key = "syrian_home_pos_secret_token_2026"
        self.token = None

    def set_token(self, token):
        self.token = token

    def get_headers(self):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-KEY": self.api_key,
            "Connection": "close"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, username, password):
        url = f"{self.base_url}/api/auth/login"
        try:
            res = requests.post(url, json={"login": username, "password": password}, headers=self.get_headers(), timeout=5)
            if res.status_code == 200:
                data = res.json()
                self.token = data.get("token")
                return True, data
            return False, res.json().get("message", "فشل تسجيل الدخول")
        except Exception as e:
            return False, f"خطأ في الاتصال بالخادم: {str(e)}"

    # ==========================================
    # 1. CATALOG & PRODUCTS SYNC (INITIAL DATA)
    # ==========================================
    def fetch_initial_data(self, branch_id=None):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "get_products", "api_key": self.api_key}
        if branch_id:
            params["branch_id"] = branch_id

        try:
            res = requests.get(url, headers=self.get_headers(), params=params, timeout=12)
            if res.status_code == 200:
                d = res.json()
                if d.get("success") and "products" in d:
                    cats = self.fetch_cloud_categories()
                    return True, {
                        "products": d["products"],
                        "categories": cats,
                        "stocks": [],
                        "customers": []
                    }
        except Exception as e:
            print(f"[ApiClient] Catalog pull error: {e}")
        return False, "فشل جلب البيانات من السيرفر السحابي"

    def fetch_cloud_categories(self):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "get_categories", "api_key": self.api_key}
        try:
            res = requests.get(url, headers=self.get_headers(), params=params, timeout=8)
            if res.status_code == 200:
                d = res.json()
                if d.get("success") and "categories" in d:
                    return d["categories"]
        except Exception:
            pass
        return []

    def push_product(self, prod_data):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "sync_product", "api_key": self.api_key}
        payload = {
            "name": prod_data.get("name"),
            "category": prod_data.get("category_id") or "عام",
            "sub_category": prod_data.get("sub_category", ""),
            "price": float(prod_data.get("piece_price", 0)),
            "cost": float(prod_data.get("piece_cost", 0)),
            "stock": float(prod_data.get("stock_qty", 100)),
            "barcode": prod_data.get("piece_barcode", ""),
            "barcode2": prod_data.get("carton_barcode", ""),
            "barcode3": prod_data.get("extra_barcode", ""),
            "local_code": prod_data.get("scale_code", "")
        }
        try:
            res = requests.post(url, params=params, json=payload, headers=self.get_headers(), timeout=8)
            return res.status_code == 200 and res.json().get("success", False)
        except Exception:
            return False

    def update_cloud_stock(self, barcode_or_name, new_stock):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "update_stock", "api_key": self.api_key}
        payload = {"barcode": str(barcode_or_name), "stock": float(new_stock)}
        try:
            res = requests.post(url, params=params, json=payload, headers=self.get_headers(), timeout=8)
            return res.status_code == 200 and res.json().get("success", False)
        except Exception:
            return False

    # ==========================================
    # 2. SALES / INVOICES REAL SYNC (push_sale)
    # ==========================================
    def push_sale(self, invoice_data):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "push_sale", "api_key": self.api_key}

        items_payload = []
        for it in invoice_data.get("items", []):
            name = it.get("clean_name") or it.get("product_name") or it.get("name") or "منتج"
            qty = float(it.get("quantity") or 1.0)
            if it.get("unit_sold") == "carton":
                qty *= float(it.get("units_per_carton", 1))
            items_payload.append({
                "name": name,
                "qty": qty,
                "price": float(it.get("unit_price") or 0.0),
                "barcode": it.get("barcode", ""),
                "local_code": it.get("scale_code", ""),
                "product_id": it.get("product_id")
            })

        payload = {
            "local_sale_id": invoice_data.get("invoice_number") or invoice_data.get("id"),
            "customer": invoice_data.get("customer_name") or "عميل نقدي",
            "phone": invoice_data.get("customer_phone") or "",
            "address": invoice_data.get("delivery_address") or "",
            "delivery_person": "",
            "delivery_fee": float(invoice_data.get("delivery_charge") or 0.0),
            "payment_method": invoice_data.get("payment_method") or "كاش",
            "discount": float(invoice_data.get("discount") or 0.0),
            "total": float(invoice_data.get("net_total") or 0.0),
            "date": invoice_data.get("created_at") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cashier_name": invoice_data.get("cashier_id") or "كاشير المحل",
            "source": "desktop_pos",
            "order_type": "delivery" if invoice_data.get("sale_type") == "delivery" else "hall",
            "items": items_payload
        }

        try:
            res = requests.post(url, params=params, json=payload, headers=self.get_headers(), timeout=10)
            if res.status_code == 200:
                d = res.json()
                if d.get("success"):
                    return True, d.get("invoice_barcode") or d.get("remote_id")
                return False, d.get("error", "فشل معالجة الفاتورة بالسيرفر")
            return False, f"Server HTTP {res.status_code}"
        except Exception as e:
            return False, str(e)

    def sync_invoices(self, branch_id, invoices_data, db=None):
        synced_ids = []
        for inv in invoices_data:
            success, res = self.push_sale(inv)
            if success:
                synced_ids.append(inv["id"])
                import time
                time.sleep(0.3)

        if db and synced_ids:
            db.mark_invoices_synced(synced_ids)

        return True, synced_ids

    # ==========================================
    # 3. PURCHASES REAL SYNC (push_purchase)
    # ==========================================
    def push_purchase(self, purchase_data):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "push_purchase", "api_key": self.api_key}

        items_payload = []
        for it in purchase_data.get("items", []):
            items_payload.append({
                "name": it.get("name") or "صنف توريد",
                "barcode": it.get("barcode", ""),
                "qty": float(it.get("piece_qty", 1.0)) + float(it.get("bonus_qty", 0.0)),
                "cost_price": float(it.get("buy_price", 0.0)),
                "selling_price": float(it.get("sell_price", 0.0)),
                "total_cost": float(it.get("total_cost", 0.0))
            })

        payload = {
            "supplier_name": purchase_data.get("supplier_name", "مورد عام"),
            "supplier_id": 0,
            "invoice_number": purchase_data.get("invoice_number", f"PUR-{int(time.time())}"),
            "payment_method": purchase_data.get("payment_method", "نقدي"),
            "total_amount": float(purchase_data.get("total_amount", 0.0)),
            "paid_amount": float(purchase_data.get("paid_amount", 0.0)),
            "discount": float(purchase_data.get("discount", 0.0)),
            "date": purchase_data.get("created_at") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "desktop_pos",
            "items": items_payload
        }

        try:
            res = requests.post(url, params=params, json=payload, headers=self.get_headers(), timeout=10)
            if res.status_code == 200:
                d = res.json()
                if d.get("success"):
                    return True, d.get("purchase_id")
                return False, d.get("error", "فشل حفظ فاتورة المشتريات بالسيرفر")
            return False, f"Server HTTP {res.status_code}"
        except Exception as e:
            return False, str(e)

    def fetch_cloud_purchases(self, limit=50):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "get_purchases", "limit": limit, "api_key": self.api_key}
        try:
            res = requests.get(url, params=params, headers=self.get_headers(), timeout=8)
            if res.status_code == 200:
                d = res.json()
                if d.get("success") and "purchases" in d:
                    return True, d["purchases"]
        except Exception as e:
            return False, str(e)
        return False, []

    def sync_purchases(self, db):
        pushed = 0
        pulled = 0
        unsynced = db.get_unsynced_purchases()
        synced_ids = []
        for pur in unsynced:
            success, _ = self.push_purchase(pur)
            if success:
                synced_ids.append(pur["id"])
                pushed += 1
                import time
                time.sleep(0.3)
        if synced_ids:
            db.mark_purchases_synced(synced_ids)

        success_pull, cloud_purchases = self.fetch_cloud_purchases(limit=50)
        if success_pull and isinstance(cloud_purchases, list):
            pulled = db.sync_cloud_purchases(cloud_purchases)

        return True, {"pushed": pushed, "pulled": pulled}

    # ==========================================
    # 4. CUSTOMERS SYNC (save_customer / get_customers)
    # ==========================================
    def push_customer(self, cust_data):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "save_customer", "api_key": self.api_key}
        payload = {
            "name": cust_data.get("name", "").strip(),
            "phone": cust_data.get("phone", "").strip(),
            "address": cust_data.get("address", "") or "",
            "notes": "مسجل من كاشير المحل"
        }
        try:
            res = requests.post(url, params=params, json=payload, headers=self.get_headers(), timeout=8)
            if res.status_code == 200 and res.json().get("success"):
                return True, res.json().get("customer_id")
        except Exception:
            pass
        return False, None

    def fetch_cloud_customers(self, limit=200):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "get_customers", "limit": limit, "api_key": self.api_key}
        try:
            res = requests.get(url, params=params, headers=self.get_headers(), timeout=10)
            if res.status_code == 200:
                d = res.json()
                if d.get("success") and "customers" in d:
                    return True, d["customers"]
        except Exception as e:
            return False, str(e)
        return False, []

    def sync_customers(self, db):
        pushed = 0
        pulled = 0
        unsynced = db.get_unsynced_customers()
        synced_ids = []
        for cust in unsynced:
            success, _ = self.push_customer(cust)
            if success:
                synced_ids.append(cust["id"])
                pushed += 1
                import time
                time.sleep(0.2)
        if synced_ids:
            db.mark_customers_synced(synced_ids)

        success_pull, cloud_custs = self.fetch_cloud_customers(limit=200)
        if success_pull and isinstance(cloud_custs, list):
            pulled = db.sync_cloud_customers(cloud_custs)

        return True, {"pushed": pushed, "pulled": pulled}

    # ==========================================
    # 5. SUPPLIERS SYNC (sync_supplier / get_suppliers / pay_supplier)
    # ==========================================
    def push_supplier(self, supp_data):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "sync_supplier", "api_key": self.api_key}
        payload = {
            "name": supp_data.get("name", "").strip(),
            "phone": supp_data.get("phone", "").strip(),
            "balance": float(supp_data.get("current_balance", 0.0))
        }
        try:
            res = requests.post(url, params=params, json=payload, headers=self.get_headers(), timeout=8)
            if res.status_code == 200 and res.json().get("success"):
                return True, res.json().get("supplier_id")
        except Exception:
            pass
        return False, None

    def push_supplier_payment(self, supplier_name, amount, note="", payment_method="كاش"):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "pay_supplier", "api_key": self.api_key}
        payload = {
            "supplier_name": supplier_name,
            "amount": float(amount),
            "note": note,
            "payment_method": payment_method,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            res = requests.post(url, params=params, json=payload, headers=self.get_headers(), timeout=8)
            return res.status_code == 200 and res.json().get("success", False)
        except Exception:
            return False

    def fetch_cloud_suppliers(self):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "get_suppliers", "api_key": self.api_key}
        try:
            res = requests.get(url, params=params, headers=self.get_headers(), timeout=8)
            if res.status_code == 200:
                d = res.json()
                if d.get("success") and "suppliers" in d:
                    return True, d["suppliers"]
        except Exception as e:
            return False, str(e)
        return False, []

    def sync_suppliers(self, db):
        pushed = 0
        pulled = 0
        unsynced = db.get_unsynced_suppliers()
        synced_ids = []
        for s in unsynced:
            success, _ = self.push_supplier(s)
            if success:
                synced_ids.append(s["id"])
                pushed += 1
                import time
                time.sleep(0.2)
        if synced_ids:
            db.mark_suppliers_synced(synced_ids)

        success_pull, cloud_supps = self.fetch_cloud_suppliers()
        if success_pull and isinstance(cloud_supps, list):
            pulled = db.sync_cloud_suppliers(cloud_supps)

        return True, {"pushed": pushed, "pulled": pulled}

    # ==========================================
    # 6. WEB ORDERS (Online Store Orders)
    # ==========================================
    def fetch_cloud_orders(self, limit=50):
        url = f"{self.base_url}/api_sync.php"
        params = {"action": "get_orders", "limit": limit, "api_key": self.api_key}
        try:
            res = requests.get(url, params=params, headers=self.get_headers(), timeout=10)
            if res.status_code == 200:
                d = res.json()
                if d.get("success") and "orders" in d:
                    return True, d["orders"]
        except Exception as e:
            return False, str(e)
        return False, []

    # ==========================================
    # EXPENSES CLOUD SYNCHRONIZATION
    # ==========================================
    def push_expense(self, category, amount, note="", payment_method="كاش", date=None):
        """
        Pushes an expense record to central cloud database (MySQL) via api_sync.php?action=record_expense
        """
        url = f"{self.base_url}/api_sync.php"
        params = {
            "action": "record_expense",
            "api_key": self.api_key
        }
        payload = {
            "category": category,
            "amount": float(amount),
            "note": note,
            "payment_method": payment_method,
            "date": date or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            res = requests.post(url, params=params, json=payload, headers=self.get_headers(), timeout=8)
            if res.status_code == 200:
                data = res.json()
                if data.get("success"):
                    return True, data.get("message", "تم تسجيل المصروف سحابياً بنجاح")
                return False, data.get("error", "فشل تسجيل المصروف بالسيرفر")
            return False, f"رمز استجابة السيرفر: {res.status_code}"
        except Exception as e:
            return False, f"خطأ بالاتصال بالسيرفر السحابي: {str(e)}"

    def fetch_cloud_expenses(self, period="all"):
        """
        Pulls all recorded expenses from central cloud server
        """
        url = f"{self.base_url}/api_sync.php"
        params = {
            "action": "get_pos_reports",
            "period": period,
            "api_key": self.api_key
        }

        try:
            res = requests.get(url, params=params, headers=self.get_headers(), timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("success"):
                    exp_report = data.get("expenses_report", {})
                    expenses = exp_report.get("filtered_expenses", [])
                    return True, expenses
                return False, data.get("error", "فشل استرجاع المصروفات")
            return False, f"رمز استجابة السيرفر: {res.status_code}"
        except Exception as e:
            return False, f"خطأ بالاتصال بالسيرفر السحابي: {str(e)}"

    def sync_expenses(self, db):
        """
        Performs full bi-directional sync of expenses between local SQLite and cloud MySQL:
        1. Push unsynced local expenses to cloud.
        2. Pull cloud expenses and insert/merge them into local SQLite.
        """
        pushed_count = 0
        pulled_count = 0

        # 1. Push Unsynced Local Expenses
        unsynced = db.get_unsynced_expenses()
        synced_ids = []
        for exp in unsynced:
            cat = exp.get("category", "نثريات")
            amt = float(exp.get("amount", 0))
            note = exp.get("description", "")
            pm = exp.get("payment_method", "كاش")
            dt = exp.get("created_at")

            success, _ = self.push_expense(cat, amt, note, pm, dt)
            if success:
                synced_ids.append(exp["id"])
                pushed_count += 1

        if synced_ids:
            db.mark_expenses_synced(synced_ids)

        # 2. Pull Cloud Expenses to Local DB
        success_pull, cloud_expenses = self.fetch_cloud_expenses(period="all")
        if success_pull and isinstance(cloud_expenses, list):
            pulled_count = db.sync_cloud_expenses(cloud_expenses)

        return True, {
            "pushed": pushed_count,
            "pulled": pulled_count,
            "total_cloud": len(cloud_expenses) if success_pull and isinstance(cloud_expenses, list) else 0
        }
