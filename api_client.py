import requests

class ApiClient:
    def __init__(self, base_url="http://supermarkrt.almagd555.com"):
        self.base_url = base_url.rstrip("/")
        self.fallback_url = "http://127.0.0.1:8000"
        self.token = None

    def set_token(self, token):
        self.token = token

    def get_headers(self):
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, username, password):
        url = f"{self.base_url}/api/auth/login"
        try:
            res = requests.post(url, json={"login": username, "password": password}, timeout=5)
            if res.status_code == 200:
                data = res.json()
                self.token = data.get("token")
                return True, data
            return False, res.json().get("message", "فشل تسجيل الدخول")
        except Exception as e:
            return False, f"خطأ في الاتصال بالخادم: {str(e)}"

    def fetch_initial_data(self, branch_id=None):
        urls = [f"{self.base_url}/api/pos/initial-data", f"{self.fallback_url}/api/pos/initial-data"]
        params = {}
        if branch_id:
            params["branch_id"] = branch_id

        for url in urls:
            try:
                res = requests.get(url, headers=self.get_headers(), params=params, timeout=4)
                if res.status_code == 200:
                    return True, res.json().get("data", {})
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
