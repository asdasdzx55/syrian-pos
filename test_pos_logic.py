import unittest
import os
import uuid
import tempfile
from database import LocalDatabase

class TestPosLogic(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.db = LocalDatabase(self.db_path)

        categories = [{"id": "cat-1", "name": "مواد غذائية"}]
        products = [
            {
                "id": "prod-1",
                "name": "زيت زيتون ممتاز",
                "unit_type": "pcs",
                "has_multi_unit": True,
                "piece_barcode": "6291001",
                "carton_barcode": "6291001-CT",
                "units_per_carton": 12,
                "piece_price": 50.00,
                "piece_cost": 40.00,
                "carton_price": 570.00,
                "carton_cost": 450.00,
            },
            {
                "id": "prod-scale",
                "name": "تفاح احمر بلدي",
                "unit_type": "kg",
                "has_multi_unit": False,
                "piece_barcode": "00001",
                "piece_price": 15.00,
                "piece_cost": 10.00,
            }
        ]
        stocks = [
            {"product_id": "prod-1", "quantity_pieces": 120.0},
            {"product_id": "prod-scale", "quantity_pieces": 50.0},
        ]
        customers = [
            {"id": "cust-1", "name": "أحمد علي", "phone": "01099887766", "address": "الميدان - دمشق"}
        ]
        self.db.sync_catalog(categories, products, stocks, customers)

    def tearDown(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception:
            pass

    def test_customer_phone_lookup(self):
        cust = self.db.get_customer_by_phone("01099887766")
        self.assertIsNotNone(cust)
        self.assertEqual(cust["name"], "أحمد علي")
        self.assertEqual(cust["address"], "الميدان - دمشق")

    def test_barcode_lookup_piece_and_carton(self):
        prods_piece = self.db.get_products("6291001")
        self.assertEqual(len(prods_piece), 1)
        self.assertEqual(prods_piece[0]["piece_barcode"], "6291001")

        prods_carton = self.db.get_products("6291001-CT")
        self.assertEqual(len(prods_carton), 1)
        self.assertEqual(prods_carton[0]["carton_barcode"], "6291001-CT")

    def test_save_invoice_and_net_profit_engine(self):
        inv_data = {
            "invoice_number": "INV-TEST-001",
            "subtotal": 570.00,
            "net_total": 570.00,
            "payment_method": "cash"
        }
        items = [
            {
                "product_id": "prod-1",
                "name": "زيت زيتون ممتاز",
                "unit_sold": "carton",
                "units_per_carton": 12,
                "quantity": 1.0,
                "unit_price": 570.00,
                "total_price": 570.00
            }
        ]

        inv_id = self.db.save_invoice(inv_data, items)
        self.assertIsNotNone(inv_id)

        # Stock deduction verification (120 - 12 = 108)
        prods = self.db.get_products("prod-1")
        self.assertEqual(prods[0]["stock_qty"], 108.0)

        # Save an operating expense
        self.db.save_expense("operating", 50.0, "فاتورة كهرباء")

        # Check Net Profit
        # Total Sales = 570.00
        # COGS = 12 pieces * 40.00 piece_cost = 480.00
        # Operating Expenses = 50.00
        # Net Profit = 570 - (480 + 50) = 40.00
        summary = self.db.get_net_profit_summary()
        self.assertEqual(summary["total_sales"], 570.00)
        self.assertEqual(summary["cogs"], 480.00)
        self.assertEqual(summary["operating_expenses"], 50.00)
        self.assertEqual(summary["net_profit"], 40.00)

    def test_scale_barcode_parsing_logic(self):
        code = "2000001012507"
        item_code = code[2:7]
        weight_grams = float(code[7:12])
        weight_kg = weight_grams / 1000.0

        prods = self.db.get_products(item_code)
        self.assertEqual(len(prods), 1)
        self.assertEqual(prods[0]["id"], "prod-scale")
        self.assertEqual(weight_kg, 1.25)

if __name__ == "__main__":
    unittest.main()
