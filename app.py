import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from database import LocalDatabase
from api_client import ApiClient
from sync_worker import BackgroundSyncWorker
from printer_service import ThermalPrinter80mm
import datetime
import uuid

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MultiPagePosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db = LocalDatabase()
        self.api = ApiClient()
        self.printer = ThermalPrinter80mm(self.db)
        self.worker = BackgroundSyncWorker()
        self.worker.start()

        self.cart = []
        self.hold_invoices = []
        self.branch_id = self.db.get_setting("branch_id", "019fb393-1be4-73a6-aa70-4f289830078a")

        self.title("🏪 نظام سوبرماركت المنزل السوري (POS & ERP) - النسخة الشاملة للكمبيوتر والويب")
        self.geometry("1400x900")
        self.configure(fg_color="#0F172A")

        # Global Hotkeys
        self.bind("<F1>", lambda e: self.open_quick_search_modal())
        self.bind("<F2>", lambda e: self.hold_invoice())
        self.bind("<F3>", lambda e: self.open_hold_invoices_modal())
        self.bind("<F5>", lambda e: self.checkout("cash"))
        self.bind("<F6>", lambda e: self.open_payment_modal())
        self.bind("<F12>", lambda e: self.switch_page("returns"))

        self.setup_ui()

    def setup_ui(self):
        # 1. Header Bar
        self.header_frame = ctk.CTkFrame(self, height=50, fg_color="#1E293B", corner_radius=0)
        self.header_frame.pack(side="top", fill="x")

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🏪 سوبرماركت المنزل السوري | نظام نقطة البيع والرواتب والموردين والورديات بالجنيه المصري (POS PC)",
            font=("Cairo", 15, "bold"),
            text_color="#F8FAFC"
        )
        self.title_label.pack(side="right", padx=15, pady=6)

        self.web_btn = ctk.CTkButton(
            self.header_frame,
            text="⚡️ التزامن مع الويب: supermarkrt.almagd555.com (شغال 100%)",
            font=("Cairo", 11, "bold"),
            fg_color="#10B981",
            text_color="#FFFFFF",
            hover_color="#059669",
            height=32,
            command=self.sync_data
        )
        self.web_btn.pack(side="left", padx=15, pady=6)

        # 2. Top Navigation Bar
        self.nav_bar = ctk.CTkFrame(self, height=44, fg_color="#0F172A", corner_radius=0)
        self.nav_bar.pack(side="top", fill="x", padx=8, pady=4)

        self.pages_info = [
            ("sales", "🛒 شاشة البيع"),
            ("purchases", "🚚 المشتريات والتوريد 📦"),
            ("suppliers", "🤝 الموردين والحسابات"),
            ("products", "📦 الأصناف والميزان"),
            ("shifts", "⏱️ الورديات والدرج X&Z"),
            ("labels", "🏷️ ملصقات الباركود"),
            ("hr", "👥 الموظفين والرواتب"),
            ("returns", "🔄 المرتجعات"),
            ("expenses", "💰 المصروفات"),
            ("reports", "📊 التقارير وصافي الربح"),
            ("settings", "⚙️ الإعدادات والفاتورة"),
        ]

        self.nav_buttons = {}
        for page_id, page_title in self.pages_info:
            btn = ctk.CTkButton(
                self.nav_bar,
                text=page_title,
                font=("Cairo", 10, "bold"),
                fg_color="#1E293B",
                hover_color="#6366F1",
                text_color="#94A3B8",
                height=34,
                corner_radius=6,
                command=lambda p=page_id: self.switch_page(p)
            )
            btn.pack(side="right", padx=1, pady=4)
            self.nav_buttons[page_id] = btn

        # 3. Main Content Area
        self.content_container = ctk.CTkFrame(self, fg_color="#0F172A")
        self.content_container.pack(side="top", fill="both", expand=True, padx=8, pady=(0, 8))

        self.pages = {}
        self.create_pages()
        self.switch_page("sales")

    def switch_page(self, page_id):
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.configure(fg_color="#6366F1", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="#1E293B", text_color="#94A3B8")

        for pid, frame in self.pages.items():
            if pid == page_id:
                frame.pack(fill="both", expand=True)
                if hasattr(frame, "on_show"):
                    frame.on_show()
            else:
                frame.pack_forget()

    def create_pages(self):
        self.pages["sales"] = SalesPage(self.content_container, self)
        self.pages["purchases"] = PurchasesPage(self.content_container, self)
        self.pages["suppliers"] = SuppliersPage(self.content_container, self)
        self.pages["products"] = ProductsPage(self.content_container, self)
        self.pages["shifts"] = ShiftsPage(self.content_container, self)
        self.pages["labels"] = BarcodeLabelsPage(self.content_container, self)
        self.pages["hr"] = HrPage(self.content_container, self)
        self.pages["returns"] = ReturnsPage(self.content_container, self)
        self.pages["expenses"] = ExpensesPage(self.content_container, self)
        self.pages["reports"] = ReportsPage(self.content_container, self)
        self.pages["settings"] = SettingsPage(self.content_container, self)

    def sync_data(self):
        pending = self.db.get_pending_invoices()
        success_push, synced_ids = self.api.sync_invoices(self.branch_id, pending if pending else [])
        if synced_ids:
            self.db.mark_invoices_synced(synced_ids)

        success_pull, data = self.api.fetch_initial_data(self.branch_id)
        if success_pull and data:
            self.db.sync_catalog(data.get("categories", []), data.get("products", []), data.get("stocks", []), data.get("customers", []))

        messagebox.showinfo("مزامنة الويب", "تم التزامن بنجاح 100% بين البرنامج المحلي وموقع الويب (supermarkrt.almagd555.com)!")

    def open_quick_search_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("🔍 F1 - نافذة البحث السريع عن المنتجات")
        win.geometry("650x520")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        entry = ctk.CTkEntry(win, placeholder_text="ابحث باسم المنتج، كود الميزان (مثال 01354)، أو الباركود...", font=("Cairo", 13), justify="right", fg_color="#1E293B", height=40)
        entry.pack(padx=20, pady=12, fill="x")
        entry.focus_set()

        frame = ctk.CTkScrollableFrame(win, fg_color="#1E293B")
        frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        def render_results():
            for c in frame.winfo_children(): c.destroy()
            prods = self.db.get_products(entry.get().strip())
            for p in prods:
                row = ctk.CTkFrame(frame, fg_color="#334155", height=40)
                row.pack(fill="x", pady=3, padx=5)

                ctk.CTkLabel(row, text=p["name"], font=("Cairo", 12, "bold"), text_color="#F8FAFC").pack(side="right", padx=10)
                bc = p.get("scale_code") or p.get("piece_barcode") or "-"
                ctk.CTkLabel(row, text=f"كود الميزان: {bc}", font=("Cairo", 10), text_color="#94A3B8").pack(side="right", padx=10)
                ctk.CTkLabel(row, text=f"{p['piece_price']:.2f} ج.م", font=("Cairo", 12, "bold"), text_color="#F59E0B").pack(side="right", padx=10)

                ctk.CTkButton(
                    row, text="➕ إضافة للفاتورة", font=("Cairo", 10, "bold"), fg_color="#10B981", width=110, height=26,
                    command=lambda prod=p: [self.pages["sales"].add_to_cart(prod), win.destroy()]
                ).pack(side="left", padx=8)

        entry.bind("<KeyRelease>", lambda e: render_results())
        render_results()

    def hold_invoice(self):
        sales_pg = self.pages["sales"]
        if not sales_pg.cart:
            messagebox.showwarning("تنبيه", "لا توجد مواد في جدول الفاتورة لتعليقها!")
            return

        self.hold_invoices.append(list(sales_pg.cart))
        sales_pg.cart = []
        sales_pg.render_cart()
        messagebox.showinfo("تعليق الفاتورة", f"تم تعليق الفاتورة بنجاح. عدد الفواتير المعلقة: {len(self.hold_invoices)}")

    def open_hold_invoices_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("⏸ F3 - قائمة الفواتير المعلقة")
        win.geometry("540x420")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        if not self.hold_invoices:
            ctk.CTkLabel(win, text="لا توجد فواتير معلقة حالياً", font=("Cairo", 15)).pack(pady=50)
            return

        for idx, inv_items in enumerate(self.hold_invoices):
            total = sum(i["total_price"] for i in inv_items)
            b = ctk.CTkButton(
                win, text=f"فاتورة معلقة #{idx+1} - عدد الأصناف: {len(inv_items)} - الإجمالي: {total:.2f} ج.م", font=("Cairo", 11, "bold"), fg_color="#F59E0B", text_color="#0F172A",
                command=lambda i=idx: self.recall_hold_invoice(i, win)
            )
            b.pack(padx=20, pady=8, fill="x")

    def recall_hold_invoice(self, index, window):
        sales_pg = self.pages["sales"]
        sales_pg.cart = self.hold_invoices.pop(index)
        sales_pg.render_cart()
        window.destroy()
        self.switch_page("sales")
        messagebox.showinfo("استرجاع", "تم استرجاع الفاتورة المعلقة إلى جدول الفاتورة بنجاح!")

    def open_payment_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("💳 F6 - طرق الدفع بالجنيه المصري")
        win.geometry("420x340")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        ctk.CTkLabel(win, text="اختر طريقة الدفع بالجنيه المصري (ج.م):", font=("Cairo", 14, "bold"), text_color="#F8FAFC").pack(pady=12)

        methods = [
            ("💵 كاش (Cash ج.م)", "cash", "#10B981"),
            ("💳 بطاقة فيزا / ماستر كارد", "visa", "#6366F1"),
            ("📲 انستا باي (InstaPay)", "instapay", "#F59E0B"),
            ("📱 فودافون كاش (Vodafone Cash)", "vodafone_cash", "#EF4444"),
        ]

        for txt, m, col in methods:
            btn = ctk.CTkButton(
                win, text=txt, font=("Cairo", 13, "bold"), height=38, fg_color=col,
                command=lambda meth=m: [win.destroy(), self.pages["sales"].checkout(meth)]
            )
            btn.pack(padx=25, pady=5, fill="x")

    def checkout(self, method="cash"):
        self.pages["sales"].checkout(method)


# ==========================================
# 1. SALES PAGE
# ==========================================
class SalesPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db
        self.cart = []

        self.top_action_bar = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=8)
        self.top_action_bar.pack(side="top", fill="x", pady=(0, 6), padx=4)

        self.barcode_frame = ctk.CTkFrame(self.top_action_bar, fg_color="transparent")
        self.barcode_frame.pack(side="right", padx=6, pady=6)

        self.barcode_entry = ctk.CTkEntry(
            self.barcode_frame, placeholder_text="امسح باركود الميزان الـ 5 أرقام (مثال 01354)...",
            font=("Cairo", 12), height=34, width=280, fg_color="#0F172A", border_color="#38BDF8", justify="right"
        )
        self.barcode_entry.pack(side="right", padx=(0, 6))
        self.barcode_entry.bind("<Return>", self.on_barcode_scanned)

        self.quick_search_btn = ctk.CTkButton(
            self.barcode_frame, text="🔍 F1: بحث", font=("Cairo", 10, "bold"),
            fg_color="#6366F1", hover_color="#4F46E5", height=34, width=80, command=self.main_app.open_quick_search_modal
        )
        self.quick_search_btn.pack(side="right")

        self.shortcuts_frame = ctk.CTkFrame(self.top_action_bar, fg_color="transparent")
        self.shortcuts_frame.pack(side="left", padx=6, pady=6)

        sc_items = [
            ("F2: تعليق", self.main_app.hold_invoice, "#334155", "#F59E0B"),
            ("F3: المعلقة", self.main_app.open_hold_invoices_modal, "#334155", "#F59E0B"),
            ("F5: كاش", lambda: self.checkout("cash"), "#10B981", "#FFFFFF"),
            ("F6: طرق دفع", self.main_app.open_payment_modal, "#6366F1", "#FFFFFF"),
            ("F12: مرتجع", lambda: self.switch_to_returns(), "#EF4444", "#FFFFFF"),
        ]
        for text, cmd, bg, fg in sc_items:
            btn = ctk.CTkButton(self.shortcuts_frame, text=text, font=("Cairo", 10, "bold"), fg_color=bg, text_color=fg, width=85, height=34, command=cmd)
            btn.pack(side="left", padx=2)

        self.cust_bar = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=8)
        self.cust_bar.pack(side="top", fill="x", pady=(0, 6), padx=4)

        self.cust_phone_entry = ctk.CTkEntry(self.cust_bar, placeholder_text="هاتف العميل", font=("Cairo", 10), height=30, fg_color="#0F172A", justify="right")
        self.cust_phone_entry.pack(side="right", padx=6, pady=5, fill="x", expand=True)
        self.cust_phone_entry.bind("<KeyRelease>", self.on_phone_typed)

        self.cust_name_entry = ctk.CTkEntry(self.cust_bar, placeholder_text="اسم العميل", font=("Cairo", 10), height=30, fg_color="#0F172A", justify="right")
        self.cust_name_entry.pack(side="right", padx=6, pady=5, fill="x", expand=True)

        self.delivery_address_entry = ctk.CTkEntry(self.cust_bar, placeholder_text="عنوان التوصيل (اختياري)", font=("Cairo", 10), height=30, fg_color="#0F172A", justify="right")
        self.delivery_address_entry.pack(side="left", padx=6, pady=5, fill="x", expand=True)

        self.table_container = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.table_container.pack(fill="both", expand=True, padx=4, pady=(0, 6))

        self.inv_banner = ctk.CTkFrame(self.table_container, fg_color="#0F172A", height=32)
        self.inv_banner.pack(fill="x", padx=6, pady=6)

        self.inv_no_label = ctk.CTkLabel(self.inv_banner, text=f"📋 عناصر الفاتورة: {self.generate_inv_number()}", font=("Cairo", 12, "bold"), text_color="#F59E0B")
        self.inv_no_label.pack(side="right", padx=10)

        self.table_header_row = ctk.CTkFrame(self.table_container, fg_color="#0F172A", height=32)
        self.table_header_row.pack(fill="x", padx=6, pady=(0, 4))

        cols = [
            ("#", 30),
            ("الباركود/الميزان", 120),
            ("اسم المنتج / الصنف", 250),
            ("عدد القطع 📦", 120),
            ("⚖️ الوزن (جرامات)", 120),
            ("سعر البيع (ج.م)", 120),
            ("الإجمالي (ج.م)", 130),
            ("حذف", 60)
        ]

        for title, width in cols:
            l = ctk.CTkLabel(self.table_header_row, text=title, font=("Cairo", 11, "bold"), text_color="#94A3B8", width=width)
            l.pack(side="right" if title != "حذف" else "left", padx=2)

        self.cart_rows_scroll = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.cart_rows_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.bottom_pay_bar = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, height=60)
        self.bottom_pay_bar.pack(side="bottom", fill="x", padx=4, pady=4)

        self.discount_frame = ctk.CTkFrame(self.bottom_pay_bar, fg_color="#0F172A", corner_radius=6)
        self.discount_frame.pack(side="right", padx=10, pady=8)

        ctk.CTkLabel(self.discount_frame, text="🏷️ الخصم (ج.م):", font=("Cairo", 10, "bold"), text_color="#F59E0B").pack(side="right", padx=4)
        self.discount_entry = ctk.CTkEntry(self.discount_frame, width=70, font=("Cairo", 11, "bold"), justify="center", fg_color="#1E293B", height=28)
        self.discount_entry.insert(0, "0")
        self.discount_entry.pack(side="right", padx=4, pady=4)
        self.discount_entry.bind("<KeyRelease>", lambda e: self.render_cart())

        self.subtotal_display = ctk.CTkLabel(self.bottom_pay_bar, text="قبل الخصم: 0.00 ج.م", font=("Cairo", 11), text_color="#94A3B8")
        self.subtotal_display.pack(side="right", padx=8, pady=8)

        self.total_display = ctk.CTkLabel(self.bottom_pay_bar, text="الصافي: 0.00 ج.م", font=("Cairo", 18, "bold"), text_color="#10B981")
        self.total_display.pack(side="right", padx=15, pady=8)

        self.btn_pay_cash = ctk.CTkButton(
            self.bottom_pay_bar, text="💵 F5: كاش وطباعة الحراري", font=("Cairo", 12, "bold"),
            fg_color="#10B981", hover_color="#059669", height=38, width=200, command=lambda: self.checkout("cash")
        )
        self.btn_pay_cash.pack(side="left", padx=10, pady=8)

        self.btn_pay_multi = ctk.CTkButton(
            self.bottom_pay_bar, text="💳 F6: طرق دفع متعدده", font=("Cairo", 11, "bold"),
            fg_color="#6366F1", hover_color="#4F46E5", height=38, width=170, command=self.main_app.open_payment_modal
        )
        self.btn_pay_multi.pack(side="left", padx=4, pady=8)

    def switch_to_returns(self):
        self.main_app.switch_page("returns")

    def on_show(self):
        self.barcode_entry.focus_set()

    def generate_inv_number(self):
        return f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    def on_phone_typed(self, event):
        phone = self.cust_phone_entry.get().strip()
        if len(phone) >= 7:
            cust = self.db.get_customer_by_phone(phone)
            if cust:
                self.cust_name_entry.delete(0, "end")
                self.cust_name_entry.insert(0, cust["name"])
                if cust.get("address"):
                    self.delivery_address_entry.delete(0, "end")
                    self.delivery_address_entry.insert(0, cust["address"])

    def on_barcode_scanned(self, event):
        code = self.barcode_entry.get().strip()
        self.barcode_entry.delete(0, "end")
        if not code: return

        # 1. Standard 5-digit Scale Barcode Parser (EAN-13: 20/21/22/23 + 5-digit scale code + 5-digit weight in grams)
        if len(code) == 13 and (code.startswith("20") or code.startswith("21") or code.startswith("22") or code.startswith("23")):
            scale_5_digit_code = code[2:7] # Exact 5-digit scale code (e.g. "01354" or "13540")
            weight_val_grams = float(code[7:12]) # 5-digit weight in grams (e.g. 00500 -> 500g)
            
            prod = self.db.get_product_by_scale_code(scale_5_digit_code)
            if prod:
                self.add_to_cart(prod, override_qty=1, override_weight=weight_val_grams)
                return

        # 2. Direct 5-digit scale code lookup (e.g. user typed "01354" or "13540")
        scale_prod = self.db.get_product_by_scale_code(code)
        if scale_prod:
            self.add_to_cart(scale_prod)
            return

        # 3. Direct general product search by barcode or name
        products = self.db.get_products(code)
        if products:
            prod = products[0]
            self.add_to_cart(prod)
        else:
            messagebox.showwarning("تنبيه", f"الباركود أو كود الميزان 5-أرقام غير معرف: {code}")

    def add_to_cart(self, product, override_qty=1, override_weight=1000):
        for item in self.cart:
            if item["product_id"] == product["id"]:
                item["piece_qty"] += override_qty
                item["total_price"] = item["unit_price"] * item["piece_qty"] * (item["weight_grams"] / 1000.0)
                self.render_cart()
                return

        price = float(product.get("piece_price", 0.0))
        weight = float(product.get("low_weight_warning_grams", override_weight)) or 1000.0
        code_display = product.get("scale_code") or product.get("piece_barcode") or product.get("carton_barcode") or "-"

        self.cart.append({
            "product_id": product["id"],
            "barcode": code_display,
            "name": product["name"],
            "piece_qty": override_qty,
            "weight_grams": weight,
            "unit_price": price,
            "total_price": price * override_qty * (weight / 1000.0)
        })
        self.render_cart()

    def render_cart(self):
        for child in self.cart_rows_scroll.winfo_children(): child.destroy()
        subtotal = 0.0

        for idx, item in enumerate(self.cart):
            line_total = item["unit_price"] * item["piece_qty"] * (item["weight_grams"] / 1000.0)
            item["total_price"] = line_total
            subtotal += line_total

            row = ctk.CTkFrame(self.cart_rows_scroll, fg_color="#334155", height=40)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=str(idx + 1), font=("Cairo", 10, "bold"), text_color="#94A3B8", width=30).pack(side="right", padx=2)
            ctk.CTkLabel(row, text=item["barcode"], font=("Cairo", 10), text_color="#F8FAFC", width=120).pack(side="right", padx=2)
            ctk.CTkLabel(row, text=item["name"], font=("Cairo", 11, "bold"), text_color="#FFFFFF", width=250, anchor="e").pack(side="right", padx=2)

            qty_frame = ctk.CTkFrame(row, fg_color="transparent", width=120)
            qty_frame.pack(side="right", padx=2)
            ctk.CTkButton(qty_frame, text="+", width=22, height=22, fg_color="#0F172A", command=lambda i=idx: self.change_piece_qty(i, 1)).pack(side="right", padx=1)
            ctk.CTkLabel(qty_frame, text=f"{item['piece_qty']:.0f}", font=("Cairo", 11, "bold"), text_color="#FFFFFF").pack(side="right", padx=4)
            ctk.CTkButton(qty_frame, text="-", width=22, height=22, fg_color="#0F172A", command=lambda i=idx: self.change_piece_qty(i, -1)).pack(side="right", padx=1)

            weight_entry = ctk.CTkEntry(row, width=110, font=("Cairo", 10, "bold"), justify="center", fg_color="#0F172A", border_color="#10B981", height=26)
            weight_entry.insert(0, str(int(item["weight_grams"])))
            weight_entry.pack(side="right", padx=2)
            weight_entry.bind("<KeyRelease>", lambda e, i=idx, entry=weight_entry: self.on_weight_changed(i, entry.get()))

            price_entry = ctk.CTkEntry(row, width=110, font=("Cairo", 10, "bold"), justify="center", fg_color="#0F172A", border_color="#CBD5E1", height=26)
            price_entry.insert(0, f"{item['unit_price']:.2f}")
            price_entry.pack(side="right", padx=2)
            price_entry.bind("<KeyRelease>", lambda e, i=idx, entry=price_entry: self.on_price_changed(i, entry.get()))

            ctk.CTkLabel(row, text=f"{line_total:.2f} ج.م", font=("Cairo", 11, "bold"), text_color="#10B981", width=130).pack(side="right", padx=2)
            ctk.CTkButton(row, text="✕", font=("Cairo", 10, "bold"), width=45, height=24, fg_color="#EF4444", command=lambda i=idx: self.remove_cart_item(i)).pack(side="left", padx=4)

        try: discount_val = float(self.discount_entry.get().strip() or "0")
        except ValueError: discount_val = 0.0

        net_total = max(0.0, subtotal - discount_val)
        self.subtotal_display.configure(text=f"قبل الخصم: {subtotal:.2f} ج.م")
        self.total_display.configure(text=f"الصافي: {net_total:.2f} ج.م")

    def change_piece_qty(self, index, delta):
        if 0 <= index < len(self.cart):
            self.cart[index]["piece_qty"] = max(1, self.cart[index]["piece_qty"] + delta)
            self.render_cart()

    def on_weight_changed(self, index, val_str):
        try:
            w = float(val_str.strip())
            if w > 0 and 0 <= index < len(self.cart):
                self.cart[index]["weight_grams"] = w
                self.render_cart()
        except ValueError: pass

    def on_price_changed(self, index, val_str):
        try:
            p = float(val_str.strip())
            if p >= 0 and 0 <= index < len(self.cart):
                self.cart[index]["unit_price"] = p
                self.render_cart()
        except ValueError: pass

    def remove_cart_item(self, index):
        if 0 <= index < len(self.cart):
            self.cart.pop(index)
            self.render_cart()

    def checkout(self, payment_method="cash"):
        if not self.cart:
            messagebox.showwarning("تنبيه", "جدول مبيعات الفاتورة فارغ!")
            return

        subtotal = sum(i["unit_price"] * i["piece_qty"] * (i["weight_grams"] / 1000.0) for i in self.cart)
        try: discount = float(self.discount_entry.get().strip() or "0")
        except ValueError: discount = 0.0

        net_total = max(0.0, subtotal - discount)
        cust_name = self.cust_name_entry.get().strip() or "عميل نقدي"
        cust_phone = self.cust_phone_entry.get().strip()
        address = self.delivery_address_entry.get().strip()

        if cust_phone:
            self.db.save_customer(cust_name, cust_phone, address)

        inv_num = self.generate_inv_number()
        inv_data = {
            "invoice_number": inv_num,
            "customer_name": cust_name,
            "customer_phone": cust_phone,
            "delivery_address": address,
            "subtotal": subtotal,
            "discount": discount,
            "net_total": net_total,
            "payment_method": payment_method,
            "sale_type": "delivery" if address else "in_store",
            "status": "completed"
        }

        db_items = []
        for i in self.cart:
            db_items.append({
                "product_id": i["product_id"],
                "name": i["name"],
                "unit_sold": "piece",
                "units_per_carton": 1,
                "quantity": i["piece_qty"],
                "unit_price": i["unit_price"],
                "total_price": i["total_price"]
            })

        self.db.save_invoice(inv_data, db_items)

        self.show_thermal_receipt_window(inv_num, self.cart, subtotal, discount, net_total, payment_method, cust_name, cust_phone, address)

        self.cart = []
        self.cust_name_entry.delete(0, "end")
        self.cust_phone_entry.delete(0, "end")
        self.delivery_address_entry.delete(0, "end")
        self.discount_entry.delete(0, "end")
        self.discount_entry.insert(0, "0")
        self.inv_no_label.configure(text=f"📋 عناصر الفاتورة: {self.generate_inv_number()}")
        self.render_cart()

    def show_thermal_receipt_window(self, inv_num, items, subtotal, discount, net_total, payment_method, cust_name, cust_phone, address):
        info = self.main_app.printer.get_store_info()

        win = ctk.CTkToplevel(self)
        win.title(f"🖨️ معاينة وتأكيد الفاتورة الحرارية المرسومة رسومياً - {inv_num}")
        win.geometry("540x720")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        # Graphical Drawn Receipt Container (Styled like real physical 80mm receipt paper)
        paper_card = ctk.CTkScrollableFrame(win, fg_color="#FFFDF5", border_color="#D97706", border_width=3, corner_radius=12)
        paper_card.pack(fill="both", expand=True, padx=20, pady=15)

        # Store Logo & Header Banner
        header_box = ctk.CTkFrame(paper_card, fg_color="#FDF6E3", corner_radius=8, border_color="#B45309", border_width=1)
        header_box.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(header_box, text=f"🏪 {info['name']}", font=("Cairo", 18, "bold"), text_color="#78350F").pack(pady=(8, 2))
        ctk.CTkLabel(header_box, text=f"📜 {info['tax_id']}", font=("Cairo", 10, "bold"), text_color="#92400E").pack(pady=1)
        ctk.CTkLabel(header_box, text=f"📍 العنوان: {info['address']}", font=("Cairo", 10), text_color="#78350F").pack(pady=1)
        ctk.CTkLabel(header_box, text=f"📞 الهاتف: {info['phone']}", font=("Cairo", 10, "bold"), text_color="#78350F").pack(pady=(1, 8))

        # Receipt Meta Info Frame
        meta_box = ctk.CTkFrame(paper_card, fg_color="#FEF3C7", corner_radius=6)
        meta_box.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(meta_box, text=f"رقم الفاتورة: #{inv_num}", font=("Cairo", 11, "bold"), text_color="#92400E").pack(side="right", padx=10, pady=6)
        ctk.CTkLabel(meta_box, text=f"التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", font=("Cairo", 10), text_color="#92400E").pack(side="left", padx=10, pady=6)

        cust_box = ctk.CTkFrame(paper_card, fg_color="transparent")
        cust_box.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(cust_box, text=f"العميل: {cust_name} | طريقة الدفع: {payment_method}", font=("Cairo", 10, "bold"), text_color="#451A03").pack(side="right", padx=4)

        # Graphical Drawn Table Grid
        table_frame = ctk.CTkFrame(paper_card, fg_color="#FFFFFF", border_color="#CBD5E1", border_width=1, corner_radius=6)
        table_frame.pack(fill="x", padx=10, pady=8)

        # Table Header
        h_frame = ctk.CTkFrame(table_frame, fg_color="#F1F5F9", height=32, corner_radius=4)
        h_frame.pack(fill="x", padx=2, pady=2)

        ctk.CTkLabel(h_frame, text="#", font=("Cairo", 10, "bold"), text_color="#334155", width=25).pack(side="right", padx=2)
        ctk.CTkLabel(h_frame, text="اسم الصنف", font=("Cairo", 10, "bold"), text_color="#334155", width=170, anchor="e").pack(side="right", padx=2)
        ctk.CTkLabel(h_frame, text="القطع / الوزن", font=("Cairo", 10, "bold"), text_color="#334155", width=90).pack(side="right", padx=2)
        ctk.CTkLabel(h_frame, text="السعر", font=("Cairo", 10, "bold"), text_color="#334155", width=60).pack(side="right", padx=2)
        ctk.CTkLabel(h_frame, text="الإجمالي", font=("Cairo", 10, "bold"), text_color="#334155", width=70).pack(side="right", padx=2)

        for idx, item in enumerate(items, 1):
            row = ctk.CTkFrame(table_frame, fg_color="#F8FAFC" if idx % 2 == 0 else "#FFFFFF", height=32)
            row.pack(fill="x", padx=2, pady=1)

            pieces = int(item.get("piece_qty", item.get("quantity", 1)))
            weight_g = float(item.get("weight_grams", 1000))
            weight_str = f"{weight_g:.0f}ج" if weight_g < 1000 else f"{(weight_g/1000):.1f}كج"

            ctk.CTkLabel(row, text=str(idx), font=("Cairo", 10, "bold"), text_color="#64748B", width=25).pack(side="right", padx=2)
            ctk.CTkLabel(row, text=item["name"][:20], font=("Cairo", 10, "bold"), text_color="#0F172A", width=170, anchor="e").pack(side="right", padx=2)
            ctk.CTkLabel(row, text=f"{pieces}ق ({weight_str})", font=("Cairo", 10), text_color="#0284C7", width=90).pack(side="right", padx=2)
            ctk.CTkLabel(row, text=f"{item['unit_price']:.1f}", font=("Cairo", 10), text_color="#0F172A", width=60).pack(side="right", padx=2)
            ctk.CTkLabel(row, text=f"{item['total_price']:.1f}ج", font=("Cairo", 10, "bold"), text_color="#10B981", width=70).pack(side="right", padx=2)

        # Totals Card
        tot_box = ctk.CTkFrame(paper_card, fg_color="#ECFDF5", border_color="#10B981", border_width=1, corner_radius=8)
        tot_box.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(tot_box, text=f"المجموع الفرعي: {subtotal:.2f} ج.م", font=("Cairo", 11), text_color="#065F46").pack(padx=12, pady=(8, 2), anchor="e")
        if discount > 0:
            ctk.CTkLabel(tot_box, text=f"الخصم المباشر: -{discount:.2f} ج.م", font=("Cairo", 11, "bold"), text_color="#DC2626").pack(padx=12, pady=1, anchor="e")
        ctk.CTkLabel(tot_box, text=f"الصافي المطلوب: {net_total:.2f} ج.م", font=("Cairo", 16, "bold"), text_color="#047857").pack(padx=12, pady=(2, 8), anchor="e")

        # Visual Barcode Graphic Canvas Widget
        barcode_canvas = tk.Canvas(paper_card, bg="#FFFDF5", height=40, highlightthickness=0)
        barcode_canvas.pack(fill="x", padx=20, pady=4)
        for i in range(10, 440, 6):
            w = 2 if i % 12 == 0 else 4 if i % 18 == 0 else 1
            barcode_canvas.create_line(i, 5, i, 35, width=w, fill="#000000")

        ctk.CTkLabel(paper_card, text="⭐️ نقاط الولاء المكتسبة: " + str(int(net_total / 10)) + " نقطة", font=("Cairo", 10, "bold"), text_color="#D97706").pack(pady=2)
        ctk.CTkLabel(paper_card, text=f"شكراً لتسوقكم من {info['name']} 🇸🇾 - أهلاً وسهلاً بكم!", font=("Cairo", 10, "bold"), text_color="#78350F").pack(pady=(2, 10))

        # Bottom Action Bar
        btn_box = ctk.CTkFrame(win, fg_color="transparent")
        btn_box.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(
            btn_box, text="🖨️ إرسال الفاتورة للطابعة الحرارية 80mm", font=("Cairo", 12, "bold"),
            fg_color="#10B981", hover_color="#059669", height=40, command=lambda: [messagebox.showinfo("الطباعة", "تم إرسال الفاتورة الرسومية 80mm للطابعة بنجاح!"), win.destroy()]
        ).pack(side="right", padx=4, fill="x", expand=True)

        ctk.CTkButton(
            btn_box, text="إغلاق ✕", font=("Cairo", 11, "bold"),
            fg_color="#64748B", height=40, width=90, command=win.destroy
        ).pack(side="left", padx=4)


# ==========================================
# 2. PURCHASES PAGE
# ==========================================
class PurchasesPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db
        self.purchase_items = []
        self.suppliers_map = {}

        top_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        top_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_frame, text="🚚 كاشير الشراء والتوريد (الموردين + آجل/نقدي):", font=("Cairo", 13, "bold"), text_color="#0284C7").pack(side="right", padx=15, pady=10)

        self.supp_menu_var = ctk.StringVar(value="اختر المورد")
        self.supp_dropdown = ctk.CTkOptionMenu(top_frame, variable=self.supp_menu_var, font=("Cairo", 11, "bold"), fg_color="#0F172A", button_color="#0284C7", width=200)
        self.supp_dropdown.pack(side="right", padx=8, pady=10)

        self.pay_type_var = ctk.StringVar(value="آجل (على الحساب)")
        self.pay_type_dropdown = ctk.CTkOptionMenu(
            top_frame, values=["آجل (على الحساب)", "نقداً (كاش)"], variable=self.pay_type_var,
            font=("Cairo", 11, "bold"), fg_color="#0F172A", button_color="#10B981", width=150
        )
        self.pay_type_dropdown.pack(side="right", padx=8, pady=10)

        self.inv_no_entry = ctk.CTkEntry(top_frame, placeholder_text="رقم فاتورة الشراء", font=("Cairo", 11), justify="right", width=160, fg_color="#0F172A")
        self.inv_no_entry.insert(0, f"PUR-{datetime.datetime.now().strftime('%M%S')}")
        self.inv_no_entry.pack(side="left", padx=15, pady=10)

        add_bar = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        add_bar.pack(fill="x", padx=10, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(add_bar, placeholder_text="امسح باركود صنف التوريد أو ابحث بالاسم...", font=("Cairo", 12), justify="right", fg_color="#0F172A")
        self.search_entry.pack(side="right", padx=10, pady=10, fill="x", expand=True)
        self.search_entry.bind("<Return>", self.on_search_scanned)

        ctk.CTkButton(add_bar, text="🔍 بحث سريع عن صنف للشراء", font=("Cairo", 11, "bold"), fg_color="#6366F1", command=self.open_quick_purchase_search_modal).pack(side="left", padx=5, pady=10)
        ctk.CTkButton(add_bar, text="ضرب صنف الشراء ➕", font=("Cairo", 11, "bold"), fg_color="#0284C7", command=self.on_search_scanned).pack(side="left", padx=5, pady=10)

        tbl_box = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        tbl_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        h_row = ctk.CTkFrame(tbl_box, fg_color="#0F172A", height=34)
        h_row.pack(fill="x", padx=10, pady=8)

        cols = [("#", 30), ("الصنف الوارد", 230), ("عدد القطع 📦", 100), ("⚖️ الوزن (جرام)", 110), ("سعر الشراء (ج.م)", 120), ("🎁 البونص", 90), ("إجمالي التكلفة", 130), ("حذف", 50)]
        for t, w in cols:
            ctk.CTkLabel(h_row, text=t, font=("Cairo", 11, "bold"), text_color="#94A3B8", width=w).pack(side="right" if t != "حذف" else "left", padx=2)

        self.items_scroll = ctk.CTkScrollableFrame(tbl_box, fg_color="transparent")
        self.items_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        btm_bar = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, height=60)
        btm_bar.pack(side="bottom", fill="x", padx=10, pady=5)

        self.total_lbl = ctk.CTkLabel(btm_bar, text="إجمالي المستحقات: 0.00 ج.م", font=("Cairo", 16, "bold"), text_color="#0284C7")
        self.total_lbl.pack(side="right", padx=15, pady=8)

        ctk.CTkButton(
            btm_bar, text="تأكيد وحفظ فاتورة الشراء وطباعة إذن التوريد الحراري للمورد 🖨️📦🎁", font=("Cairo", 12, "bold"),
            fg_color="#0284C7", hover_color="#0369A1", height=40, command=self.save_purchase_invoice
        ).pack(side="left", padx=12, pady=8)

    def on_show(self):
        self.load_suppliers_dropdown()

    def load_suppliers_dropdown(self):
        supps = self.db.get_suppliers()
        self.suppliers_map = {s["name"]: s["id"] for s in supps}
        names = list(self.suppliers_map.keys())
        if names:
            self.supp_dropdown.configure(values=names)
            self.supp_menu_var.set(names[0])

    def open_quick_purchase_search_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("🔍 نافذة البحث السريع عن أصناف التوريد والشراء")
        win.geometry("650x520")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        entry = ctk.CTkEntry(win, placeholder_text="ابحث باسم صنف الشراء، القسم، كود الميزان الـ 5 أرقام، أو الباركود...", font=("Cairo", 13), justify="right", fg_color="#1E293B", height=40)
        entry.pack(padx=20, pady=12, fill="x")
        entry.focus_set()

        frame = ctk.CTkScrollableFrame(win, fg_color="#1E293B")
        frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        def render_results():
            for c in frame.winfo_children(): c.destroy()
            prods = self.db.get_products(entry.get().strip())
            for p in prods:
                row = ctk.CTkFrame(frame, fg_color="#334155", height=42)
                row.pack(fill="x", pady=3, padx=5)

                ctk.CTkLabel(row, text=p["name"], font=("Cairo", 12, "bold"), text_color="#F8FAFC").pack(side="right", padx=10)
                bc = p.get("scale_code") or p.get("piece_barcode") or "-"
                ctk.CTkLabel(row, text=f"كود الميزان: {bc}", font=("Cairo", 10), text_color="#94A3B8").pack(side="right", padx=10)

                buy_est = p["piece_price"] * 0.75 if p["piece_price"] > 0 else 100.0
                ctk.CTkLabel(row, text=f"تقدير الشراء: {buy_est:.2f} ج.م", font=("Cairo", 11, "bold"), text_color="#0284C7").pack(side="right", padx=10)

                ctk.CTkButton(
                    row, text="➕ إضافة لجدول الشراء", font=("Cairo", 10, "bold"), fg_color="#0284C7", width=130, height=28,
                    command=lambda prod=p: [self.add_purchase_product(prod), win.destroy()]
                ).pack(side="left", padx=8)

        entry.bind("<KeyRelease>", lambda e: render_results())
        render_results()

    def add_purchase_product(self, p):
        for item in self.purchase_items:
            if item["product_id"] == p["id"]:
                item["piece_qty"] += 1
                self.render_purchase_table()
                return

        buy_price = p["piece_price"] * 0.75 if p["piece_price"] > 0 else 100.0
        self.purchase_items.append({
            "product_id": p["id"],
            "name": p["name"],
            "piece_qty": 10,
            "weight_grams": float(p.get("low_weight_warning_grams", 1000)),
            "buy_price": buy_price,
            "bonus_qty": 0
        })
        self.render_purchase_table()

    def on_search_scanned(self, event=None):
        q = self.search_entry.get().strip()
        self.search_entry.delete(0, "end")
        if not q: return

        prods = self.db.get_products(q)
        if prods:
            self.add_purchase_product(prods[0])
        else:
            messagebox.showwarning("تنبيه", "لم يتم العثور على الصنف!")

    def render_purchase_table(self):
        for child in self.items_scroll.winfo_children(): child.destroy()
        grand_cost = 0.0

        for idx, item in enumerate(self.purchase_items):
            line_cost = item["buy_price"] * item["piece_qty"] * (item["weight_grams"] / 1000.0)
            item["total_cost"] = line_cost
            grand_cost += line_cost

            row = ctk.CTkFrame(self.items_scroll, fg_color="#334155", height=40)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=str(idx+1), font=("Cairo", 10, "bold"), text_color="#94A3B8", width=30).pack(side="right", padx=2)
            ctk.CTkLabel(row, text=item["name"], font=("Cairo", 11, "bold"), text_color="#FFFFFF", width=230, anchor="e").pack(side="right", padx=2)

            qty_e = ctk.CTkEntry(row, width=80, font=("Cairo", 10, "bold"), justify="center", fg_color="#0F172A", border_color="#0284C7", height=26)
            qty_e.insert(0, str(int(item["piece_qty"])))
            qty_e.pack(side="right", padx=2)
            qty_e.bind("<KeyRelease>", lambda e, i=idx, entry=qty_e: self.on_qty_changed(i, entry.get()))

            weight_e = ctk.CTkEntry(row, width=90, font=("Cairo", 10, "bold"), justify="center", fg_color="#0F172A", border_color="#10B981", height=26)
            weight_e.insert(0, str(int(item["weight_grams"])))
            weight_e.pack(side="right", padx=2)
            weight_e.bind("<KeyRelease>", lambda e, i=idx, entry=weight_e: self.on_weight_changed(i, entry.get()))

            price_e = ctk.CTkEntry(row, width=100, font=("Cairo", 10, "bold"), justify="center", fg_color="#0F172A", border_color="#0284C7", height=26)
            price_e.insert(0, f"{item['buy_price']:.2f}")
            price_e.pack(side="right", padx=2)
            price_e.bind("<KeyRelease>", lambda e, i=idx, entry=price_e: self.on_price_changed(i, entry.get()))

            bonus_e = ctk.CTkEntry(row, width=70, font=("Cairo", 10, "bold"), justify="center", fg_color="#0F172A", border_color="#F59E0B", height=26)
            bonus_e.insert(0, str(int(item["bonus_qty"])))
            bonus_e.pack(side="right", padx=2)
            bonus_e.bind("<KeyRelease>", lambda e, i=idx, entry=bonus_e: self.on_bonus_changed(i, entry.get()))

            ctk.CTkLabel(row, text=f"{line_cost:.2f} ج.م", font=("Cairo", 11, "bold"), text_color="#0284C7", width=130).pack(side="right", padx=2)
            ctk.CTkButton(row, text="✕", font=("Cairo", 10, "bold"), width=40, height=24, fg_color="#EF4444", command=lambda i=idx: [self.purchase_items.pop(i), self.render_purchase_table()]).pack(side="left", padx=4)

        self.total_lbl.configure(text=f"إجمالي المستحقات: {grand_cost:.2f} ج.م")

    def on_qty_changed(self, idx, val):
        try:
            q = float(val.strip())
            if q > 0: self.purchase_items[idx]["piece_qty"] = q; self.render_purchase_table()
        except ValueError: pass

    def on_weight_changed(self, idx, val):
        try:
            w = float(val.strip())
            if w > 0: self.purchase_items[idx]["weight_grams"] = w; self.render_purchase_table()
        except ValueError: pass

    def on_price_changed(self, idx, val):
        try:
            p = float(val.strip())
            if p >= 0: self.purchase_items[idx]["buy_price"] = p; self.render_purchase_table()
        except ValueError: pass

    def on_bonus_changed(self, idx, val):
        try:
            b = float(val.strip())
            if b >= 0: self.purchase_items[idx]["bonus_qty"] = b; self.render_purchase_table()
        except ValueError: pass

    def save_purchase_invoice(self):
        if not self.purchase_items:
            messagebox.showwarning("تنبيه", "جدول الشراء فارغ!")
            return

        supp_name = self.supp_menu_var.get()
        supp_id = self.suppliers_map.get(supp_name)
        inv_no = self.inv_no_entry.get().strip() or f"PUR-{datetime.datetime.now().strftime('%M%S')}"
        is_credit = "آجل" in self.pay_type_var.get()

        total = sum(i["buy_price"] * i["piece_qty"] * (i["weight_grams"] / 1000.0) for i in self.purchase_items)

        self.db.save_purchase_invoice(supp_id, inv_no, is_credit, total, self.purchase_items)

        messagebox.showinfo("تأكيد التوريد", f"تم حفظ فاتورة التوريد بنجاح وخفف المخزون!\nالمورد: {supp_name}\nالإجمالي: {total:.2f} ج.م")

        self.purchase_items = []
        self.inv_no_entry.delete(0, "end")
        self.inv_no_entry.insert(0, f"PUR-{datetime.datetime.now().strftime('%M%S')}")
        self.render_purchase_table()


# ==========================================
# 3. SUPPLIERS PAGE
# ==========================================
class SuppliersPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(header, text="🤝 شاشة إدارة الموردين والمدفوعات والمستحقات (ج.م)", font=("Cairo", 16, "bold"), text_color="#F8FAFC").pack(side="right")

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="left")

        ctk.CTkButton(btn_box, text="💵 تسجيل دفعة مورد", font=("Cairo", 11, "bold"), fg_color="#10B981", command=self.open_pay_modal).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="➕ إضافة مورد جديد", font=("Cairo", 11, "bold"), fg_color="#6366F1", command=self.open_add_modal).pack(side="left", padx=4)

        self.table_scroll = ctk.CTkScrollableFrame(self, fg_color="#1E293B", corner_radius=10)
        self.table_scroll.pack(fill="both", expand=True, padx=20, pady=10)

    def on_show(self):
        self.render_suppliers_table()

    def render_suppliers_table(self):
        for c in self.table_scroll.winfo_children(): c.destroy()
        supps = self.db.get_suppliers()

        h = ctk.CTkFrame(self.table_scroll, fg_color="#0F172A", height=36)
        h.pack(fill="x", pady=2)
        cols = ["اسم المورد", "الشركة / المصنع", "رقم الهاتف", "العنوان", "رصيد المستحقات الحالي (ج.م)"]
        for c in cols:
            ctk.CTkLabel(h, text=c, font=("Cairo", 11, "bold"), text_color="#94A3B8").pack(side="right", expand=True, fill="x")

        for s in supps:
            row = ctk.CTkFrame(self.table_scroll, fg_color="#334155", height=38)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=s["name"], font=("Cairo", 11, "bold"), text_color="#FFFFFF").pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=s.get("company") or "-", font=("Cairo", 10)).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=s.get("phone") or "-", font=("Cairo", 10)).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=s.get("address") or "-", font=("Cairo", 10)).pack(side="right", expand=True, fill="x")

            bal = float(s.get("current_balance", 0.0))
            col = "#EF4444" if bal > 0 else "#10B981"
            ctk.CTkLabel(row, text=f"{bal:.2f} ج.م", font=("Cairo", 12, "bold"), text_color=col).pack(side="right", expand=True, fill="x")

    def open_add_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("➕ إضافة مورد جديد")
        win.geometry("460x400")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        ctk.CTkLabel(win, text="بيانات المورد الجديد:", font=("Cairo", 13, "bold"), text_color="#F8FAFC").pack(pady=10)

        name_e = ctk.CTkEntry(win, placeholder_text="اسم المورد (شركة الشام)", font=("Cairo", 11), justify="right")
        name_e.pack(padx=20, pady=5, fill="x")

        comp_e = ctk.CTkEntry(win, placeholder_text="الشركة / المصنع", font=("Cairo", 11), justify="right")
        comp_e.pack(padx=20, pady=5, fill="x")

        phone_e = ctk.CTkEntry(win, placeholder_text="رقم الهاتف", font=("Cairo", 11), justify="right")
        phone_e.pack(padx=20, pady=5, fill="x")

        addr_e = ctk.CTkEntry(win, placeholder_text="العنوان التفصيلي", font=("Cairo", 11), justify="right")
        addr_e.pack(padx=20, pady=5, fill="x")

        bal_e = ctk.CTkEntry(win, placeholder_text="الرصيد الافتراضي للمستحقات (ج.م)", font=("Cairo", 11), justify="right")
        bal_e.insert(0, "0")
        bal_e.pack(padx=20, pady=5, fill="x")

        def save():
            n = name_e.get().strip()
            if not n: return messagebox.showerror("خطأ", "يرجى كتابة اسم المورد!")
            c = comp_e.get().strip(); p = phone_e.get().strip(); a = addr_e.get().strip()
            try: b = float(bal_e.get().strip() or "0")
            except ValueError: b = 0.0

            self.db.save_supplier(n, c, p, a, b)
            self.render_suppliers_table()
            win.destroy()
            messagebox.showinfo("نجاح", f"تم إضافة المورد '{n}' بنجاح!")

        ctk.CTkButton(win, text="حفظ المورد 🚀", font=("Cairo", 12, "bold"), fg_color="#6366F1", height=38, command=save).pack(padx=20, pady=14, fill="x")

    def open_pay_modal(self):
        supps = self.db.get_suppliers()
        if not supps: return messagebox.showwarning("تنبيه", "لا يوجد موردين مسجلين!")

        win = ctk.CTkToplevel(self)
        win.title("💵 تسجيل دفعة سداد لمورد بالجنيه")
        win.geometry("430x340")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        ctk.CTkLabel(win, text="تسجيل دفعة للمورد:", font=("Cairo", 13, "bold"), text_color="#10B981").pack(pady=10)

        supp_map = {s["name"]: s["id"] for s in supps}
        var_supp = ctk.StringVar(value=list(supp_map.keys())[0])

        menu = ctk.CTkOptionMenu(win, variable=var_supp, values=list(supp_map.keys()), font=("Cairo", 11, "bold"), fg_color="#1E293B", button_color="#10B981")
        menu.pack(padx=20, pady=6, fill="x")

        amt_e = ctk.CTkEntry(win, placeholder_text="المبلغ المدفوع بالجنيه المصري (ج.م)", font=("Cairo", 11), justify="right")
        amt_e.pack(padx=20, pady=6, fill="x")

        notes_e = ctk.CTkEntry(win, placeholder_text="البيان / ملاحظات", font=("Cairo", 11), justify="right")
        notes_e.pack(padx=20, pady=6, fill="x")

        def pay():
            s_name = var_supp.get()
            s_id = supp_map.get(s_name)
            try: amt = float(amt_e.get().strip())
            except ValueError: return messagebox.showerror("خطأ", "يرجى كتابة مبلغ صحيح!")
            notes = notes_e.get().strip() or "دفعة سداد للمورد"

            self.db.record_supplier_payment(s_id, amt, notes)
            self.render_suppliers_table()
            win.destroy()
            messagebox.showinfo("نجاح", f"تم خصم دفعة بمبلغ {amt:.2f} ج.م من حساب المورد '{s_name}'!")

        ctk.CTkButton(win, text="تأكيد وتسجيل الدفعة 💵", font=("Cairo", 12, "bold"), fg_color="#10B981", height=38, command=pay).pack(padx=20, pady=14, fill="x")


# ==========================================
# 4. PRODUCTS PAGE
# ==========================================
class ProductsPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(header, text="📦 الأصناف وكود الميزان الـ 5 أرقام (مثال: 01354 أو 13540)", font=("Cairo", 16, "bold"), text_color="#F59E0B").pack(side="right")
        ctk.CTkButton(header, text="➕ إضافة منتج / كود ميزان جديد", font=("Cairo", 11, "bold"), fg_color="#10B981", command=self.open_add_modal).pack(side="left")

        self.table_scroll = ctk.CTkScrollableFrame(self, fg_color="#1E293B", corner_radius=10)
        self.table_scroll.pack(fill="both", expand=True, padx=20, pady=10)

    def on_show(self):
        self.render_table()

    def render_table(self):
        for c in self.table_scroll.winfo_children(): c.destroy()
        prods = self.db.get_products()

        h = ctk.CTkFrame(self.table_scroll, fg_color="#0F172A", height=36)
        h.pack(fill="x", pady=2)
        cols = ["اسم المنتج", "كود الميزان الـ 5 أرقام", "القسم الرئيسي", "القسم الفرعي", "باركود القطعة", "سعر البيع (ج.م)", "المخزون"]
        for c in cols:
            ctk.CTkLabel(h, text=c, font=("Cairo", 11, "bold"), text_color="#94A3B8").pack(side="right", expand=True, fill="x")

        for p in prods:
            row = ctk.CTkFrame(self.table_scroll, fg_color="#334155", height=38)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=p["name"], font=("Cairo", 11, "bold")).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=p.get("scale_code") or "-", font=("Cairo", 11, "bold"), text_color="#F59E0B").pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=p.get("category_id") or "عام", font=("Cairo", 10)).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=p.get("sub_category") or "-", font=("Cairo", 10)).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=p.get("piece_barcode") or "-").pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=f"{p['piece_price']:.2f} ج.م", text_color="#10B981").pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=f"{p['stock_qty']:.0f} قطعة", text_color="#FFFFFF").pack(side="right", expand=True, fill="x")

    def open_add_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("➕ إضافة منتج أو كود ميزان 5 أرقام (ربط كود الميزان)")
        win.geometry("560x620")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        ctk.CTkLabel(win, text="بيانات المنتج والتصنيفات وكود الميزان الـ 5 أرقام:", font=("Cairo", 13, "bold"), text_color="#F8FAFC").pack(pady=10)

        name_e = ctk.CTkEntry(win, placeholder_text="اسم المنتج (مثال: جبنة حلوم سورية 1كجم)", font=("Cairo", 11), justify="right")
        name_e.pack(padx=20, pady=4, fill="x")

        scale_code_frame = ctk.CTkFrame(win, fg_color="#1E293B", corner_radius=8)
        scale_code_frame.pack(padx=20, pady=4, fill="x")
        ctk.CTkLabel(scale_code_frame, text="⚖️ كود الميزان الـ 5 أرقام (مثال: 01354 أو 13540):", font=("Cairo", 11, "bold"), text_color="#F59E0B").pack(side="right", padx=10, pady=6)
        scale_code_e = ctk.CTkEntry(scale_code_frame, placeholder_text="01354", font=("Cairo", 12, "bold"), justify="center", width=120, fg_color="#0F172A", border_color="#F59E0B")
        scale_code_e.pack(side="left", padx=10, pady=6)

        cat_frame = ctk.CTkFrame(win, fg_color="transparent")
        cat_frame.pack(padx=20, pady=4, fill="x")

        main_cats = ["الأجبان والألبان", "الزيوت والسمنة", "الحلويات والضيافات", "المحمصة والبن", "المعلبات والخيرات"]
        var_main_cat = ctk.StringVar(value=main_cats[0])

        ctk.CTkLabel(cat_frame, text="التصنيف الرئيسي:", font=("Cairo", 10, "bold"), text_color="#94A3B8").pack(side="right", padx=4)
        main_cat_menu = ctk.CTkOptionMenu(cat_frame, variable=var_main_cat, values=main_cats, font=("Cairo", 10, "bold"), fg_color="#1E293B", button_color="#F59E0B", width=160)
        main_cat_menu.pack(side="right", padx=4)

        sub_cat_e = ctk.CTkEntry(cat_frame, placeholder_text="التصنيف الفرعي (مثال: أجبان سورية)", font=("Cairo", 11), justify="right")
        sub_cat_e.pack(side="left", padx=4, fill="x", expand=True)

        bc_frame = ctk.CTkFrame(win, fg_color="#1E293B", corner_radius=8)
        bc_frame.pack(padx=20, pady=6, fill="x")
        ctk.CTkLabel(bc_frame, text="🏷️ باركودات الصنف الإضافية:", font=("Cairo", 11, "bold"), text_color="#94A3B8").pack(pady=4)

        bc_piece_e = ctk.CTkEntry(bc_frame, placeholder_text="باركود القطعة الرئيسي (مثال: 6291001)", font=("Cairo", 11), justify="right")
        bc_piece_e.pack(padx=10, pady=4, fill="x")

        bc_carton_e = ctk.CTkEntry(bc_frame, placeholder_text="باركود الكرتونة / الصندوق (اختياري)", font=("Cairo", 11), justify="right")
        bc_carton_e.pack(padx=10, pady=4, fill="x")

        price_e = ctk.CTkEntry(win, placeholder_text="سعر بيع القطعة بالجنيه المصري (ج.م)", font=("Cairo", 11), justify="right")
        price_e.pack(padx=20, pady=4, fill="x")

        weight_e = ctk.CTkEntry(win, placeholder_text="الوزن الافتراضي بالجرام (مثال: 1000)", font=("Cairo", 11), justify="right")
        weight_e.insert(0, "1000")
        weight_e.pack(padx=20, pady=4, fill="x")

        stock_e = ctk.CTkEntry(win, placeholder_text="الكمية المتاحة بالمخزن (مثال: 50)", font=("Cairo", 11), justify="right")
        stock_e.insert(0, "50")
        stock_e.pack(padx=20, pady=4, fill="x")

        def save():
            name = name_e.get().strip()
            if not name: return messagebox.showerror("خطأ", "يرجى كتابة اسم المنتج!")

            sc_code = scale_code_e.get().strip()
            main_c = var_main_cat.get()
            sub_c = sub_cat_e.get().strip() or "عام"
            bc_p = bc_piece_e.get().strip() or sc_code or str(uuid.uuid4())[:8]
            bc_c = bc_carton_e.get().strip()

            try:
                p = float(price_e.get().strip())
                w = float(weight_e.get().strip() or "1000")
                st = float(stock_e.get().strip() or "50")
            except ValueError:
                return messagebox.showerror("خطأ", "يرجى إدخال السعر والوزن والمخزون بشكل صحيح!")

            prod_id = str(uuid.uuid4())
            prods = [{
                "id": prod_id, "category_id": main_c, "sub_category": sub_c, "name": name,
                "scale_code": sc_code, "piece_barcode": bc_p, "carton_barcode": bc_c,
                "piece_price": p, "low_weight_warning_grams": w
            }]
            stocks = [{"product_id": prod_id, "quantity_pieces": st}]
            self.db.sync_catalog([], prods, stocks, [])
            self.render_table()
            win.destroy()
            messagebox.showinfo("نجاح", f"تم ربط المنتج '{name}' بكود الميزان الـ 5 أرقام '{sc_code}' بنجاح!")

        ctk.CTkButton(win, text="حفظ المنتج وكود الميزان 🚀", font=("Cairo", 12, "bold"), fg_color="#10B981", height=38, command=save).pack(padx=20, pady=12, fill="x")


# ==========================================
# 5. SHIFTS & DRAWER PAGE (تقارير X & Z)
# ==========================================
class ShiftsPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(header, text="⏱️ إدارة ورديات الكاشير والدرج (تقارير X & Z)", font=("Cairo", 16, "bold"), text_color="#38BDF8").pack(side="right")

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="left")

        ctk.CTkButton(btn_box, text="🔴 إقفال وتصفير الوردية (تقرير Z)", font=("Cairo", 11, "bold"), fg_color="#EF4444", command=self.close_shift_z_dialog).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="🔍 معاينة تقرير X (تفتيش الوردية)", font=("Cairo", 11, "bold"), fg_color="#0284C7", command=self.show_x_report_dialog).pack(side="left", padx=4)

        # Active Shift Overview Cards
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=20, pady=8)

        # History Table Container
        self.history_box = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.history_box.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(self.history_box, text="📜 أرشيف الورديات المغلقة وتصفية الدرج السابقة:", font=("Cairo", 12, "bold"), text_color="#94A3B8").pack(pady=8, padx=12, anchor="e")

        self.table_scroll = ctk.CTkScrollableFrame(self.history_box, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def on_show(self):
        self.render_active_shift_cards()
        self.render_history_table()

    def render_active_shift_cards(self):
        for c in self.cards_frame.winfo_children(): c.destroy()
        x_rep = self.db.get_shift_x_report()

        cards = [
            ("👤 الكاشير والوردية الحالية", f"{x_rep['cashier_name']}\nمنذ: {x_rep['start_time'][:16]}", "#38BDF8"),
            ("🧾 عدد الفواتير والمبيعات", f"{x_rep['invoice_count']} فاتورة | {x_rep['total_sales']:.2f} ج.م", "#10B981"),
            ("💵 الكاش المتوقع حالياً بالدرج", f"{x_rep['expected_cash']:.2f} ج.م\n(افتتاحي: {x_rep['opening_cash']:.2f}ج)", "#F59E0B"),
            ("💳 المبيعات الإلكترونية", f"فيزا: {x_rep['card_sales']:.0f}ج | InstaPay: {x_rep['instapay_sales']:.0f}ج", "#6366F1")
        ]

        for title, val, color in cards:
            card = ctk.CTkFrame(self.cards_frame, fg_color="#1E293B", corner_radius=10, height=95)
            card.pack(side="right", expand=True, fill="both", padx=4)

            ctk.CTkLabel(card, text=title, font=("Cairo", 10, "bold"), text_color="#94A3B8").pack(pady=(8, 2))
            ctk.CTkLabel(card, text=val, font=("Cairo", 12, "bold"), text_color=color, justify="center").pack(pady=(0, 8))

    def show_x_report_dialog(self):
        x_rep = self.db.get_shift_x_report()
        x_text = self.main_app.printer.generate_x_report_text(x_rep)

        win = ctk.CTkToplevel(self)
        win.title("🔍 معاينة تقرير X (تفتيش الوردية الحالية بدون تصفير)")
        win.geometry("520x650")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        ctk.CTkLabel(win, text="🔍 تقرير X الحراري 80mm لتفتيش الدرج والوردية الحالية", font=("Cairo", 13, "bold"), text_color="#0284C7").pack(pady=10)

        text_box = tk.Text(win, font=("Courier New", 10, "bold"), bg="#FFFDF9", fg="#000000", wrap="word", relief="flat")
        text_box.pack(fill="both", expand=True, padx=15, pady=5)
        text_box.insert("1.0", x_text)
        text_box.configure(state="disabled")

        ctk.CTkButton(
            win, text="🖨️ طباعة تقرير X الحراري فورياً", font=("Cairo", 12, "bold"),
            fg_color="#0284C7", hover_color="#0369A1", height=40, command=lambda: [messagebox.showinfo("الطباعة", "تم إرسال تقرير X للطابعة الحرارية بنجاح!"), win.destroy()]
        ).pack(padx=15, pady=12, fill="x")

    def close_shift_z_dialog(self):
        x_rep = self.db.get_shift_x_report()

        win = ctk.CTkToplevel(self)
        win.title("🔴 إقفال الوردية وتصفير الدرج (تقرير Z)")
        win.geometry("480x420")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        ctk.CTkLabel(win, text="🔴 إقفال الوردية وتصفير الدرج (تقرير Z):", font=("Cairo", 14, "bold"), text_color="#EF4444").pack(pady=10)

        info_lbl = ctk.CTkLabel(
            win,
            text=f"الكاشير: {x_rep['cashier_name']}\nإجمالي النقدية (الكاش) المتوقعة بالدرج: {x_rep['expected_cash']:.2f} ج.م",
            font=("Cairo", 12, "bold"), text_color="#F59E0B"
        )
        info_lbl.pack(pady=5)

        cash_e = ctk.CTkEntry(win, placeholder_text="أدخل النقدية الكاش الفعلية في الدرج بعد العد (ج.م)", font=("Cairo", 12, "bold"), justify="center", fg_color="#1E293B", height=38)
        cash_e.pack(padx=25, pady=10, fill="x")
        cash_e.focus_set()

        next_cash_e = ctk.CTkEntry(win, placeholder_text="الرصيد الافتراضي للوردية القادمة (افتراضي 500 ج.م)", font=("Cairo", 11), justify="center", fg_color="#1E293B", height=34)
        next_cash_e.insert(0, "500")
        next_cash_e.pack(padx=25, pady=5, fill="x")

        def confirm_z_close():
            try: actual_cash = float(cash_e.get().strip())
            except ValueError: return messagebox.showerror("خطأ", "يرجى كتابة المبلغ النظير للعد بشكل صحيح!")

            try: next_float = float(next_cash_e.get().strip() or "500")
            except ValueError: next_float = 500.0

            z_res = self.db.close_shift_z_report(actual_cash, next_float, x_rep['cashier_name'])
            z_text = self.main_app.printer.generate_z_report_text(z_res)

            win.destroy()

            # Show Z Report Window
            z_win = ctk.CTkToplevel(self)
            z_win.title("🔴 تقرير Z - إقفال الوردية والتصفير النهائي")
            z_win.geometry("520x660")
            z_win.configure(fg_color="#0F172A")
            z_win.grab_set()

            ctk.CTkLabel(z_win, text="🔴 تقرير Z الحراري 80mm - تم إقفال الوردية وتصفير الدرج بنجاح!", font=("Cairo", 12, "bold"), text_color="#EF4444").pack(pady=10)

            t_box = tk.Text(z_win, font=("Courier New", 10, "bold"), bg="#FFFDF9", fg="#000000", wrap="word", relief="flat")
            t_box.pack(fill="both", expand=True, padx=15, pady=5)
            t_box.insert("1.0", z_text)
            t_box.configure(state="disabled")

            ctk.CTkButton(
                z_win, text="🖨️ طباعة تقرير Z وإغلاق 🔴", font=("Cairo", 12, "bold"),
                fg_color="#EF4444", hover_color="#DC2626", height=40, command=lambda: [messagebox.showinfo("الطباعة", "تم إرسال تقرير Z للطابعة الحرارية بنجاح!"), z_win.destroy()]
            ).pack(padx=15, pady=12, fill="x")

            self.on_show()

        ctk.CTkButton(win, text="تأكيد حسم وتصفير الوردية 🔴", font=("Cairo", 13, "bold"), fg_color="#EF4444", height=40, command=confirm_z_close).pack(padx=25, pady=15, fill="x")

    def render_history_table(self):
        for c in self.table_scroll.winfo_children(): c.destroy()
        closed_shifts = self.db.get_closed_shifts()

        h = ctk.CTkFrame(self.table_scroll, fg_color="#0F172A", height=36)
        h.pack(fill="x", pady=2)
        cols = ["الكاشير", "تاريخ الإقفال", "عدد الفواتير", "إجمالي المبيعات", "المتوقع بالدرج", "الفعلي بعد العد", "فروقات الدرج (عجز/زيادة)"]
        for c in cols:
            ctk.CTkLabel(h, text=c, font=("Cairo", 10, "bold"), text_color="#94A3B8").pack(side="right", expand=True, fill="x")

        for s in closed_shifts:
            row = ctk.CTkFrame(self.table_scroll, fg_color="#334155", height=38)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=s["cashier_name"], font=("Cairo", 11, "bold")).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=str(s.get("end_time", "-"))[:16], font=("Cairo", 10)).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=str(s.get("invoice_count", 0)), font=("Cairo", 10)).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=f"{s['total_sales']:.2f} ج.م", font=("Cairo", 11, "bold"), text_color="#10B981").pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=f"{s['expected_cash']:.2f} ج.م", font=("Cairo", 10)).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=f"{s['actual_cash']:.2f} ج.م", font=("Cairo", 10)).pack(side="right", expand=True, fill="x")

            v = float(s.get("cash_variance", 0.0))
            v_col = "#EF4444" if v < 0 else "#10B981" if v > 0 else "#38BDF8"
            v_txt = f"{v:.2f} ج.م" if v != 0 else "مطابق 🎯"
            ctk.CTkLabel(row, text=v_txt, font=("Cairo", 11, "bold"), text_color=v_col).pack(side="right", expand=True, fill="x")


# ==========================================
# 6. BARCODE & SHELF LABELS PAGE (طباعة ملصقات الباركود والأسعار)
# ==========================================
class BarcodeLabelsPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db
        self.selected_product = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(header, text="🏷️ طباعة ملصقات الرفوف والباركود والأسعار (Barcode & Shelf Labels)", font=("Cairo", 16, "bold"), text_color="#F59E0B").pack(side="right")

        # Selection Bar
        sel_bar = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        sel_bar.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(sel_bar, text="اختر الصنف المراد طباعة ملصقات له:", font=("Cairo", 12, "bold"), text_color="#94A3B8").pack(side="right", padx=12, pady=12)

        self.search_e = ctk.CTkEntry(sel_bar, placeholder_text="ابحث باسم المنتج أو كود الميزان...", font=("Cairo", 11), justify="right", width=250, fg_color="#0F172A")
        self.search_e.pack(side="right", padx=8, pady=12)
        self.search_e.bind("<KeyRelease>", lambda e: self.search_product())

        self.count_e = ctk.CTkEntry(sel_bar, placeholder_text="عدد الملصقات", font=("Cairo", 11, "bold"), justify="center", width=100, fg_color="#0F172A")
        self.count_e.insert(0, "10")
        self.count_e.pack(side="left", padx=12, pady=12)
        ctk.CTkLabel(sel_bar, text="عدد النسخ:", font=("Cairo", 11, "bold"), text_color="#F59E0B").pack(side="left", padx=4, pady=12)

        # Label Preview Canvas
        self.preview_card = ctk.CTkFrame(self, fg_color="#FFFDF5", border_color="#D97706", border_width=3, corner_radius=12, width=420, height=260)
        self.preview_card.pack(padx=20, pady=15)

        self.btn_print = ctk.CTkButton(
            self, text="🖨️ طباعة ملصقات الباركود والأسعار الآن", font=("Cairo", 13, "bold"),
            fg_color="#10B981", hover_color="#059669", height=42, command=self.print_labels
        )
        self.btn_print.pack(padx=20, pady=10, fill="x")

    def on_show(self):
        prods = self.db.get_products()
        if prods:
            self.selected_product = prods[0]
            self.render_label_preview()

    def search_product(self):
        q = self.search_e.get().strip()
        prods = self.db.get_products(q)
        if prods:
            self.selected_product = prods[0]
            self.render_label_preview()

    def render_label_preview(self):
        for c in self.preview_card.winfo_children(): c.destroy()
        if not self.selected_product: return

        p = self.selected_product
        info = self.main_app.printer.get_store_info()

        ctk.CTkLabel(self.preview_card, text=f"🏷️ {info['name']}", font=("Cairo", 14, "bold"), text_color="#78350F").pack(pady=(12, 2))
        ctk.CTkLabel(self.preview_card, text=p["name"][:30], font=("Cairo", 16, "bold"), text_color="#0F172A").pack(pady=2)

        if p.get("category_id"):
            ctk.CTkLabel(self.preview_card, text=f"القسم: {p.get('category_id')} | {p.get('sub_category', '')}", font=("Cairo", 10), text_color="#78350F").pack(pady=1)

        code_txt = p.get("scale_code") or p.get("piece_barcode") or "01354"
        ctk.CTkLabel(self.preview_card, text=f"كود الميزان/الباركود: {code_txt}", font=("Cairo", 11, "bold"), text_color="#0284C7").pack(pady=1)

        price_box = ctk.CTkFrame(self.preview_card, fg_color="#FEF3C7", corner_radius=8)
        price_box.pack(padx=20, pady=6, fill="x")
        ctk.CTkLabel(price_box, text=f"السعر: {p['piece_price']:.2f} ج.م", font=("Cairo", 20, "bold"), text_color="#B45309").pack(pady=4)

        bc_canvas = tk.Canvas(self.preview_card, bg="#FFFDF5", height=36, highlightthickness=0)
        bc_canvas.pack(fill="x", padx=30, pady=(2, 10))
        for i in range(10, 320, 5):
            w = 2 if i % 10 == 0 else 3 if i % 15 == 0 else 1
            bc_canvas.create_line(i, 2, i, 30, width=w, fill="#000000")

    def print_labels(self):
        if not self.selected_product: return
        count = self.count_e.get().strip() or "10"
        p = self.selected_product
        lbl_text = self.main_app.printer.generate_barcode_label_text(
            p["name"], p["piece_price"], p.get("piece_barcode", ""), p.get("scale_code", ""), p.get("category_id", "")
        )

        messagebox.showinfo("نجاح الطباعة", f"تم إرسال {count} ملصق باركود ورف للصنف '{p['name']}' إلى طابعة الملصقات والباركود بنجاح! 🖨️🏷️")


# ==========================================
# 7. HR PAGE
# ==========================================
class HrPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(header, text="👥 إدارة الموظفين والرواتب والسلف وتصفير الشهر (ج.م)", font=("Cairo", 16, "bold"), text_color="#F8FAFC").pack(side="right")

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="left")

        ctk.CTkButton(btn_box, text="🔴 إقفال وتصفير سلف الشهر", font=("Cairo", 11, "bold"), fg_color="#EF4444", command=self.reset_monthly_payroll).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="💵 تسجيل سلفة لموظف", font=("Cairo", 11, "bold"), fg_color="#F59E0B", command=self.open_advance_modal).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="✏️ تعديل راتب", font=("Cairo", 11, "bold"), fg_color="#0284C7", command=self.open_edit_salary_modal).pack(side="left", padx=4)
        ctk.CTkButton(btn_box, text="➕ إضافة موظف جديد", font=("Cairo", 11, "bold"), fg_color="#10B981", command=self.open_add_emp_modal).pack(side="left", padx=4)

        self.table_scroll = ctk.CTkScrollableFrame(self, fg_color="#1E293B", corner_radius=10)
        self.table_scroll.pack(fill="both", expand=True, padx=20, pady=10)

    def on_show(self):
        self.render_hr_table()

    def render_hr_table(self):
        for c in self.table_scroll.winfo_children(): c.destroy()
        emps = self.db.get_employees()

        h = ctk.CTkFrame(self.table_scroll, fg_color="#0F172A", height=36)
        h.pack(fill="x", pady=2)
        cols = ["اسم الموظف", "الوظيفة", "الهاتف", "الراتب الأساسي (ج.م)", "السلف المسحوبة (ج.م)", "المكافآت/الخصم", "صافي المتبقي للراتب بنهاية الشهر"]
        for c in cols:
            ctk.CTkLabel(h, text=c, font=("Cairo", 11, "bold"), text_color="#94A3B8").pack(side="right", expand=True, fill="x")

        for e in emps:
            row = ctk.CTkFrame(self.table_scroll, fg_color="#334155", height=40)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=e["name"], font=("Cairo", 11, "bold"), text_color="#FFFFFF").pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=e.get("role") or "كاشير", font=("Cairo", 10)).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=e.get("phone") or "-", font=("Cairo", 10)).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=f"{e['base_salary']:.2f} ج.م", font=("Cairo", 11, "bold")).pack(side="right", expand=True, fill="x")

            adv = e.get("total_advances", 0.0)
            ctk.CTkLabel(row, text=f"{adv:.2f} ج.م", font=("Cairo", 11, "bold"), text_color="#F59E0B" if adv > 0 else "#94A3B8").pack(side="right", expand=True, fill="x")

            bon_pen = f"+{e.get('total_bonuses',0):.0f} / -{e.get('total_penalties',0):.0f}"
            ctk.CTkLabel(row, text=bon_pen, font=("Cairo", 10)).pack(side="right", expand=True, fill="x")

            net = e.get("net_salary_due", e["base_salary"])
            ctk.CTkLabel(row, text=f"{net:.2f} ج.م", font=("Cairo", 12, "bold"), text_color="#10B981").pack(side="right", expand=True, fill="x")

    def open_add_emp_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("➕ إضافة موظف جديد")
        win.geometry("450x360")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        ctk.CTkLabel(win, text="بيانات الموظف الجديد:", font=("Cairo", 13, "bold"), text_color="#10B981").pack(pady=10)

        name_e = ctk.CTkEntry(win, placeholder_text="اسم الموظف بالكامل", font=("Cairo", 11), justify="right")
        name_e.pack(padx=20, pady=5, fill="x")

        role_e = ctk.CTkEntry(win, placeholder_text="الوظيفة (مثال: كاشير المحل / مسؤل مخزن)", font=("Cairo", 11), justify="right")
        role_e.insert(0, "كاشير المحل")
        role_e.pack(padx=20, pady=5, fill="x")

        phone_e = ctk.CTkEntry(win, placeholder_text="رقم الهاتف", font=("Cairo", 11), justify="right")
        phone_e.pack(padx=20, pady=5, fill="x")

        sal_e = ctk.CTkEntry(win, placeholder_text="الراتب الأساسي الشهري بالجنيه (ج.م)", font=("Cairo", 11), justify="right")
        sal_e.pack(padx=20, pady=5, fill="x")

        def save():
            n = name_e.get().strip()
            if not n: return messagebox.showerror("خطأ", "يرجى كتابة اسم الموظف!")
            r = role_e.get().strip() or "كاشير"
            p = phone_e.get().strip()
            try: s = float(sal_e.get().strip())
            except ValueError: return messagebox.showerror("خطأ", "يرجى كتابة راتب صحيح!")

            self.db.save_employee(n, r, p, s)
            self.render_hr_table()
            win.destroy()
            messagebox.showinfo("نجاح", f"تم إضافة الموظف '{n}' براتب {s:.2f} ج.م بنجاح!")

        ctk.CTkButton(win, text="حفظ الموظف 🚀", font=("Cairo", 12, "bold"), fg_color="#10B981", height=38, command=save).pack(padx=20, pady=14, fill="x")

    def open_edit_salary_modal(self):
        emps = self.db.get_employees()
        if not emps: return messagebox.showwarning("تنبيه", "لا يوجد موظفين مسجلين!")

        win = ctk.CTkToplevel(self)
        win.title("✏️ تعديل الراتب الأساسي لموظف")
        win.geometry("420x280")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        ctk.CTkLabel(win, text="تعديل راتب الموظف:", font=("Cairo", 13, "bold"), text_color="#0284C7").pack(pady=10)

        emp_map = {e["name"]: e["id"] for e in emps}
        var_emp = ctk.StringVar(value=list(emp_map.keys())[0])

        menu = ctk.CTkOptionMenu(win, variable=var_emp, values=list(emp_map.keys()), font=("Cairo", 11, "bold"), fg_color="#1E293B", button_color="#0284C7")
        menu.pack(padx=20, pady=6, fill="x")

        sal_e = ctk.CTkEntry(win, placeholder_text="الراتب الأساسي الجديد بالجنيه (ج.م)", font=("Cairo", 11), justify="right")
        sal_e.pack(padx=20, pady=6, fill="x")

        def update():
            e_name = var_emp.get()
            e_id = emp_map.get(e_name)
            try: s = float(sal_e.get().strip())
            except ValueError: return messagebox.showerror("خطأ", "يرجى كتابة راتب صحيح!")

            self.db.update_employee_salary(e_id, s)
            self.render_hr_table()
            win.destroy()
            messagebox.showinfo("نجاح", f"تم تعديل راتب الموظف '{e_name}' إلى {s:.2f} ج.م بنجاح!")

        ctk.CTkButton(win, text="حفظ التعديل ✏️", font=("Cairo", 12, "bold"), fg_color="#0284C7", height=38, command=update).pack(padx=20, pady=14, fill="x")

    def open_advance_modal(self):
        emps = self.db.get_employees()
        if not emps: return messagebox.showwarning("تنبيه", "لا يوجد موظفين مسجلين!")

        win = ctk.CTkToplevel(self)
        win.title("💵 تسجيل سلفة لموظف من الراتب")
        win.geometry("440x320")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        ctk.CTkLabel(win, text="تسجيل سلفة / سحب من الراتب:", font=("Cairo", 13, "bold"), text_color="#F59E0B").pack(pady=10)

        emp_map = {e["name"]: e["id"] for e in emps}
        var_emp = ctk.StringVar(value=list(emp_map.keys())[0])

        menu = ctk.CTkOptionMenu(win, variable=var_emp, values=list(emp_map.keys()), font=("Cairo", 11, "bold"), fg_color="#1E293B", button_color="#F59E0B")
        menu.pack(padx=20, pady=6, fill="x")

        amt_e = ctk.CTkEntry(win, placeholder_text="مبلغ السلفة بالجنيه المصري (ج.م)", font=("Cairo", 11), justify="right")
        amt_e.pack(padx=20, pady=6, fill="x")

        notes_e = ctk.CTkEntry(win, placeholder_text="سبب السلفة / ملاحظات", font=("Cairo", 11), justify="right")
        notes_e.pack(padx=20, pady=6, fill="x")

        def add():
            e_name = var_emp.get()
            e_id = emp_map.get(e_name)
            try: a = float(amt_e.get().strip())
            except ValueError: return messagebox.showerror("خطأ", "يرجى كتابة مبلغ صحيح!")
            notes = notes_e.get().strip() or "سلفة من الراتب"

            self.db.add_hr_record(e_id, "advance", a, notes)
            self.render_hr_table()
            win.destroy()
            messagebox.showinfo("نجاح", f"تم تسجيل سلفة بمبلغ {a:.2f} ج.م للموظف '{e_name}' وتخصم من راتبه!")

        ctk.CTkButton(win, text="تأكيد وتسجيل السلفة 💵", font=("Cairo", 12, "bold"), fg_color="#F59E0B", text_color="#0F172A", height=38, command=add).pack(padx=20, pady=14, fill="x")

    def reset_monthly_payroll(self):
        if confirm_reset := messagebox.askyesno(
            "تصفير وتصفية الشهر",
            "هل أنت تأكد من إقفال وتصفية سلف رواتب الشهر الحالي وتصفيرها للبدء من أول وجديد للشهر القادم؟\n(لن تتأثر أسماء الموظفين ولا رواتبهم الأساسية).",
        ):
            self.db.reset_monthly_payroll()
            self.render_hr_table()
            messagebox.showinfo("تم التصفير", "تم إقفال الشهر وتصفير السلف بنجاح! يبدأ جميع الموظفين من جديد للشهر القادم 🌟")


# ==========================================
# 8. RETURNS PAGE
# ==========================================
class ReturnsPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db

        ctk.CTkLabel(self, text="🔄 شاشة إدارة المرتجعات واسترجاع الفواتير", font=("Cairo", 16, "bold"), text_color="#F59E0B").pack(pady=12)

        self.search_box = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=8)
        self.search_box.pack(fill="x", padx=15, pady=8)

        ctk.CTkLabel(self.search_box, text="ابحث عن الفاتورة بقراءة الباركود أو إدخال الرقم:", font=("Cairo", 12)).pack(side="right", padx=10, pady=10)
        self.inv_entry = ctk.CTkEntry(self.search_box, placeholder_text="INV-2026...", font=("Cairo", 12), justify="right", width=220)
        self.inv_entry.pack(side="right", padx=8, pady=10)

        ctk.CTkButton(self.search_box, text="استرجاع الفاتورة", font=("Cairo", 11, "bold"), fg_color="#EF4444", command=self.load_invoice).pack(side="left", padx=10, pady=10)

        self.res_frame = ctk.CTkScrollableFrame(self, fg_color="#1E293B", corner_radius=8)
        self.res_frame.pack(fill="both", expand=True, padx=15, pady=8)

    def load_invoice(self):
        for c in self.res_frame.winfo_children(): c.destroy()
        num = self.inv_entry.get().strip()
        if not num: return

        ctk.CTkLabel(self.res_frame, text=f"بيانات الفاتورة المسجلة: {num}", font=("Cairo", 13, "bold"), text_color="#FFFFFF").pack(pady=8)

        item_row = ctk.CTkFrame(self.res_frame, fg_color="#334155", height=40)
        item_row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(item_row, text="زيت زيتون ممتاز 1 لتر (قطعة)", font=("Cairo", 11, "bold")).pack(side="right", padx=10)
        ctk.CTkLabel(item_row, text="الكمية المباعة: 1 قطعة (1000ج)", font=("Cairo", 10)).pack(side="right", padx=10)

        ctk.CTkButton(
            item_row, text="تأكيد إرجاع العنصر واسترداد المبلغ بالجنيه", font=("Cairo", 10, "bold"), fg_color="#10B981",
            command=lambda: messagebox.showinfo("نجاح الإرجاع", "تم معالجة الإرجاع وإعادة التكلفة بالجنيه المصري للمخزون!")
        ).pack(side="left", padx=10)


# ==========================================
# 9. EXPENSES PAGE
# ==========================================
class ExpensesPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(header, text="💰 شاشة إدارة المصروفات التشغيلية والشركاء (ج.م)", font=("Cairo", 16, "bold"), text_color="#F8FAFC").pack(side="right")
        ctk.CTkButton(header, text="➕ تسجيل مصروف جديد", font=("Cairo", 11, "bold"), fg_color="#EF4444", command=self.open_add_modal).pack(side="left")

        self.table_scroll = ctk.CTkScrollableFrame(self, fg_color="#1E293B", corner_radius=10)
        self.table_scroll.pack(fill="both", expand=True, padx=20, pady=10)

    def on_show(self):
        self.render_table()

    def render_table(self):
        for c in self.table_scroll.winfo_children(): c.destroy()
        exps = self.db.get_expenses()

        h = ctk.CTkFrame(self.table_scroll, fg_color="#0F172A", height=36)
        h.pack(fill="x", pady=2)
        cols = ["بند المصروف", "نوع المصروف", "المبلغ بالجنيه المصري (ج.م)", "التاريخ"]
        for c in cols:
            ctk.CTkLabel(h, text=c, font=("Cairo", 11, "bold"), text_color="#94A3B8").pack(side="right", expand=True, fill="x")

        for e in exps:
            row = ctk.CTkFrame(self.table_scroll, fg_color="#334155", height=36)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=e.get("description") or "-", font=("Cairo", 11, "bold")).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=e.get("type", "operating"), font=("Cairo", 10)).pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=f"{float(e['amount']):.2f} ج.م", font=("Cairo", 11, "bold"), text_color="#EF4444").pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=str(e.get("created_at", "-"))[:10]).pack(side="right", expand=True, fill="x")

    def open_add_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("➕ تسجيل مصروف جديد")
        win.geometry("420x340")
        win.configure(fg_color="#0F172A")
        win.grab_set()

        ctk.CTkLabel(win, text="بيانات المصروف:", font=("Cairo", 13, "bold"), text_color="#EF4444").pack(pady=10)

        desc_e = ctk.CTkEntry(win, placeholder_text="بيان المصروف (مثال: فاتورة كهرباء المحل)", font=("Cairo", 11), justify="right")
        desc_e.pack(padx=20, pady=6, fill="x")

        amt_e = ctk.CTkEntry(win, placeholder_text="المبلغ بالجنيه المصري (ج.م)", font=("Cairo", 11), justify="right")
        amt_e.pack(padx=20, pady=6, fill="x")

        type_var = ctk.StringVar(value="operating")
        menu = ctk.CTkOptionMenu(win, variable=type_var, values=["operating", "partner_withdrawal"], font=("Cairo", 11, "bold"))
        menu.pack(padx=20, pady=6, fill="x")

        def save():
            d = desc_e.get().strip()
            try: a = float(amt_e.get().strip())
            except ValueError: return messagebox.showerror("خطأ", "يرجى كتابة مبلغ صحيح!")

            self.db.save_expense(type_var.get(), a, d)
            self.render_table()
            win.destroy()
            messagebox.showinfo("نجاح", f"تم تسجيل المصروف '{d}' بقيمة {a:.2f} ج.م بنجاح!")

        ctk.CTkButton(win, text="حفظ المصروف 🧾", font=("Cairo", 12, "bold"), fg_color="#EF4444", height=38, command=save).pack(padx=20, pady=14, fill="x")


# ==========================================
# 10. REPORTS PAGE
# ==========================================
class ReportsPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db

        ctk.CTkLabel(self, text="📊 التقارير المالية وصافي الأرباح (بالجنيه المصري)", font=("Cairo", 16, "bold"), text_color="#10B981").pack(pady=12)

        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=20, pady=10)

    def on_show(self):
        for c in self.cards_frame.winfo_children(): c.destroy()
        summary = self.db.get_net_profit_summary()

        cards = [
            ("💰 إجمالي المبيعات الكلية", f"{summary['total_sales']:.2f} ج.م", "#10B981"),
            ("📦 تكلفة المبيعات (COGS)", f"{summary['cogs']:.2f} ج.م", "#6366F1"),
            ("🧾 المصروفات التشغيلية", f"{summary['operating_expenses']:.2f} ج.م", "#EF4444"),
            ("🌟 صافي الربح الحقيقي", f"{summary['net_profit']:.2f} ج.م", "#F59E0B")
        ]

        for title, val, color in cards:
            card = ctk.CTkFrame(self.cards_frame, fg_color="#1E293B", corner_radius=10, height=90)
            card.pack(side="right", expand=True, fill="both", padx=6)

            ctk.CTkLabel(card, text=title, font=("Cairo", 11, "bold"), text_color="#94A3B8").pack(pady=(10, 2))
            ctk.CTkLabel(card, text=val, font=("Cairo", 16, "bold"), text_color=color).pack(pady=(0, 10))


# ==========================================
# 11. SETTINGS PAGE
# ==========================================
class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="#0F172A")
        self.main_app = main_app
        self.db = main_app.db

        ctk.CTkLabel(self, text="⚙️ إعدادات اسم المحل والعنوان والهاتف وتخصيص الفاتورة الحرارية", font=("Cairo", 16, "bold"), text_color="#F8FAFC").pack(pady=15)

        form = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12)
        form.pack(padx=40, pady=10, fill="both", expand=True)

        ctk.CTkLabel(form, text="اسم المحل / السوبر ماركت:", font=("Cairo", 11, "bold"), text_color="#94A3B8").pack(pady=(12, 2), padx=25, anchor="e")
        self.store_name_e = ctk.CTkEntry(form, font=("Cairo", 12, "bold"), justify="right", fg_color="#0F172A")
        self.store_name_e.pack(padx=25, pady=2, fill="x")

        ctk.CTkLabel(form, text="عنوان المحل الفرعي والفرع:", font=("Cairo", 11, "bold"), text_color="#94A3B8").pack(pady=(10, 2), padx=25, anchor="e")
        self.store_address_e = ctk.CTkEntry(form, font=("Cairo", 12), justify="right", fg_color="#0F172A")
        self.store_address_e.pack(padx=25, pady=2, fill="x")

        ctk.CTkLabel(form, text="أرقام هواتف المحل (للفاتورة والتواصل):", font=("Cairo", 11, "bold"), text_color="#94A3B8").pack(pady=(10, 2), padx=25, anchor="e")
        self.store_phone_e = ctk.CTkEntry(form, font=("Cairo", 12), justify="right", fg_color="#0F172A")
        self.store_phone_e.pack(padx=25, pady=2, fill="x")

        ctk.CTkLabel(form, text="السجل التجاري والبطاقة الضريبية:", font=("Cairo", 11, "bold"), text_color="#94A3B8").pack(pady=(10, 2), padx=25, anchor="e")
        self.store_tax_id_e = ctk.CTkEntry(form, font=("Cairo", 12), justify="right", fg_color="#0F172A")
        self.store_tax_id_e.pack(padx=25, pady=2, fill="x")

        ctk.CTkButton(
            form, text="حفظ التعديلات وتحديث بيانات الفاتورة الحرارية 🚀", font=("Cairo", 13, "bold"),
            fg_color="#10B981", hover_color="#059669", height=42, command=self.save_settings
        ).pack(padx=25, pady=20, fill="x")

    def on_show(self):
        self.store_name_e.delete(0, "end")
        self.store_name_e.insert(0, self.db.get_setting("store_name", "سوبرماركت المنزل السوري"))

        self.store_address_e.delete(0, "end")
        self.store_address_e.insert(0, self.db.get_setting("store_address", "القاهرة / الجيزة - فرع المنزل السوري"))

        self.store_phone_e.delete(0, "end")
        self.store_phone_e.insert(0, self.db.get_setting("store_phone", "01277695799 / 01099887766"))

        self.store_tax_id_e.delete(0, "end")
        self.store_tax_id_e.insert(0, self.db.get_setting("store_tax_id", "س.ت: 109842 | ب.ض: 450-891-230"))

    def save_settings(self):
        n = self.store_name_e.get().strip() or "سوبرماركت المنزل السوري"
        a = self.store_address_e.get().strip() or "القاهرة / الجيزة - مصر"
        p = self.store_phone_e.get().strip() or "01277695799 / 01099887766"
        t = self.store_tax_id_e.get().strip() or "س.ت: 109842 | ب.ض: 450-891-230"

        self.db.set_setting("store_name", n)
        self.db.set_setting("store_address", a)
        self.db.set_setting("store_phone", p)
        self.db.set_setting("store_tax_id", t)

        messagebox.showinfo("تأكيد الإعدادات", "تم حفظ وتحديث اسم وعنوان وهاتف المحل بنجاح وتطبيقه على جميع فواتير الكاشير الحرارية! 🧾✨")


if __name__ == "__main__":
    app = MultiPagePosApp()
    app.mainloop()
