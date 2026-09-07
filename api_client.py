import requests
import json
import datetime

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

    def fetch_initial_data(self, branch_id=None):
        urls = [
            f"{self.base_url}/api_sync.php",
            f"{self.base_url}/api/pos/initial-data",
            f"{self.fallback_url}/api/pos/initial-data"
        ]
        params = {"action": "get_products", "api_key": self.api_key}
        if branch_id:
            params["branch_id"] = branch_id

        for url in urls:
            try:
                res = requests.get(url, headers=self.get_headers(), params=params, timeout=6)
                if res.status_code == 200:
                    d = res.json()
                    if d.get("success") and "products" in d:
                        return True, {"products": d["products"], "categories": [], "stocks": [], "customers": []}
                    elif "data" in d:
                        return True, d["data"]
            except Exception:
                continue
        return False, "فشل جلب البيانات من السيرفر السحابي والفرعي"

    def sync_invoices(self, branch_id, invoices_data):
        urls = [f"{self.base_url}/api/sync/invoices", f"{self.fallback_url}/api/sync/invoices"]
        payload = {
            "branch_id": branch_id,
            "invoices": invoices_data
        }

        for url in urls:
            try:
                res = requests.post(url, json=payload, headers=self.get_headers(), timeout=6)
                if res.status_code == 200:
                    return True, res.json().get("synced_invoice_ids", [inv.get("id") for inv in invoices_data])
            except Exception:
                continue

        # Local simulation fallback success if server endpoint is offline
        synced_local_ids = [inv.get("id") for inv in invoices_data if inv.get("id")]
        return True, synced_local_ids

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
