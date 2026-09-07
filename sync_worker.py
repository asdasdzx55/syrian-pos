import threading
import time
from database import LocalDatabase
from api_client import ApiClient

class BackgroundSyncWorker:
    def __init__(self, db_path="pos_local.db", base_url="https://supermarkrt.almagd555.com", interval_seconds=20):
        self.db = LocalDatabase(db_path)
        self.api = ApiClient(base_url)
        self.interval = interval_seconds
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False

    def sync_now(self):
        branch_id = self.db.get_setting("branch_id", "019fb393-1be4-73a6-aa70-4f289830078a")
        sync_report = {}

        # 1. Push Pending Sales / Invoices (action=push_sale)
        try:
            pending = self.db.get_pending_invoices()
            if pending:
                success, synced_ids = self.api.sync_invoices(branch_id, pending, db=self.db)
                sync_report["sales_pushed"] = len(synced_ids)
                if synced_ids:
                    print(f"[Sync Worker] Pushed {len(synced_ids)} sales invoices to cloud.")
        except Exception as e:
            print(f"[Sync Worker] Sales sync error: {e}")

        # 2. Synchronize Expenses Bi-Directionally (action=record_expense & get_pos_reports)
        try:
            exp_success, exp_res = self.api.sync_expenses(self.db)
            if exp_success:
                sync_report["expenses"] = exp_res
                if exp_res.get("pushed", 0) > 0 or exp_res.get("pulled", 0) > 0:
                    print(f"[Sync Worker] Expenses Synced: Pushed {exp_res.get('pushed')}, Pulled {exp_res.get('pulled')}")
        except Exception as e:
            print(f"[Sync Worker] Expense sync note: {e}")

        # 3. Synchronize Purchases (action=push_purchase & get_purchases)
        try:
            pur_success, pur_res = self.api.sync_purchases(self.db)
            if pur_success:
                sync_report["purchases"] = pur_res
                if pur_res.get("pushed", 0) > 0 or pur_res.get("pulled", 0) > 0:
                    print(f"[Sync Worker] Purchases Synced: Pushed {pur_res.get('pushed')}, Pulled {pur_res.get('pulled')}")
        except Exception as e:
            print(f"[Sync Worker] Purchases sync error: {e}")

        # 4. Synchronize Customers (action=save_customer & get_customers)
        try:
            cust_success, cust_res = self.api.sync_customers(self.db)
            if cust_success:
                sync_report["customers"] = cust_res
                if cust_res.get("pushed", 0) > 0 or cust_res.get("pulled", 0) > 0:
                    print(f"[Sync Worker] Customers Synced: Pushed {cust_res.get('pushed')}, Pulled {cust_res.get('pulled')}")
        except Exception as e:
            print(f"[Sync Worker] Customers sync error: {e}")

        # 5. Synchronize Suppliers (action=sync_supplier & get_suppliers)
        try:
            supp_success, supp_res = self.api.sync_suppliers(self.db)
            if supp_success:
                sync_report["suppliers"] = supp_res
                if supp_res.get("pushed", 0) > 0 or supp_res.get("pulled", 0) > 0:
                    print(f"[Sync Worker] Suppliers Synced: Pushed {supp_res.get('pushed')}, Pulled {supp_res.get('pulled')}")
        except Exception as e:
            print(f"[Sync Worker] Suppliers sync error: {e}")

        # 6. Pull Latest Central Catalog & Stock (action=get_products & get_categories)
        try:
            success, data = self.api.fetch_initial_data(branch_id)
            if success and data:
                categories = data.get("categories", [])
                products = data.get("products", [])
                stocks = data.get("stocks", [])
                customers = data.get("customers", [])
                if categories or products:
                    self.db.sync_catalog(categories, products, stocks, customers)
                    sync_report["catalog_updated"] = True
                    print("[Sync Worker] Pulled central catalog updates.")
        except Exception as e:
            print(f"[Sync Worker] Catalog pull error: {e}")

        # 7. Check Web Orders (action=get_orders)
        try:
            success_orders, web_orders = self.api.fetch_cloud_orders(limit=20)
            if success_orders and isinstance(web_orders, list):
                sync_report["web_orders_count"] = len(web_orders)
        except Exception as e:
            print(f"[Sync Worker] Web orders check error: {e}")

        return sync_report

    def _run_loop(self):
        while self.running:
            try:
                self.sync_now()
            except Exception as e:
                print(f"[Sync Worker Warning] Sync attempt failed: {e}")
            time.sleep(self.interval)

if __name__ == "__main__":
    worker = BackgroundSyncWorker()
    worker.start()
    print("Background Sync Worker started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
            # Run manual test
            worker.sync_now()
            break
    except KeyboardInterrupt:
        worker.stop()
        print("Sync Worker stopped.")
