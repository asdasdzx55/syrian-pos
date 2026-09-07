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
        
        # 1. Push Pending Invoices
        pending = self.db.get_pending_invoices()
        if pending:
            success, synced_ids = self.api.sync_invoices(branch_id, pending)
            if success and synced_ids:
                self.db.mark_invoices_synced(synced_ids)
                print(f"[Sync Worker] Successfully pushed {len(synced_ids)} offline invoices to central server.")

        # 2. Pull Latest Central Catalog & Stock
        success, data = self.api.fetch_initial_data(branch_id)
        if success and data:
            categories = data.get("categories", [])
            products = data.get("products", [])
            stocks = data.get("stocks", [])
            customers = data.get("customers", [])
            if categories or products:
                self.db.sync_catalog(categories, products, stocks, customers)
                print("[Sync Worker] Successfully pulled central catalog & stock updates.")

        # 3. Synchronize Expenses Bi-Directionally (Local POS <-> Cloud Web)
        try:
            exp_success, exp_res = self.api.sync_expenses(self.db)
            if exp_success and (exp_res.get("pushed", 0) > 0 or exp_res.get("pulled", 0) > 0):
                print(f"[Sync Worker] Expenses Synced: Pushed {exp_res.get('pushed')}, Pulled {exp_res.get('pulled')}")
        except Exception as e:
            print(f"[Sync Worker] Expense sync note: {e}")

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
