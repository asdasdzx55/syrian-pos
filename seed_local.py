from database import LocalDatabase

def seed():
    db = LocalDatabase()
    
    categories = [
        {"id": "cat-1", "name": "المواد الغذائية", "description": "منتجات غذائية أساسية"},
        {"id": "cat-2", "name": "أجبان وألبان", "description": "أجبان طازجة ومشروبات"},
        {"id": "cat-3", "name": "خضار وفواكه وميزان", "description": "خضار بالوزن"},
    ]

    products = [
        {
            "id": "prod-1",
            "category_id": "cat-1",
            "name": "زيت زيتون ممتاز 1 لتر",
            "unit_type": "pcs",
            "has_multi_unit": True,
            "piece_barcode": "6291001",
            "carton_barcode": "6291001-CT",
            "units_per_carton": 12,
            "piece_price": 250.00,
            "piece_cost": 190.00,
            "carton_price": 2850.00,
            "carton_cost": 2200.00,
            "is_active": True
        },
        {
            "id": "prod-2",
            "category_id": "cat-2",
            "name": "حليب كامل الدسم 1L",
            "unit_type": "pcs",
            "has_multi_unit": True,
            "piece_barcode": "111111",
            "carton_barcode": "111111-CT",
            "units_per_carton": 10,
            "piece_price": 45.00,
            "piece_cost": 36.00,
            "carton_price": 430.00,
            "carton_cost": 350.00,
            "is_active": True
        },
        {
            "id": "prod-3",
            "category_id": "cat-3",
            "name": "تفاح أحمر بلدي (ميزان)",
            "unit_type": "kg",
            "has_multi_unit": False,
            "piece_barcode": "00001",
            "carton_barcode": None,
            "units_per_carton": 1,
            "piece_price": 60.00,
            "piece_cost": 42.00,
            "is_active": True
        }
    ]

    stocks = [
        {"product_id": "prod-1", "quantity_pieces": 120.0},
        {"product_id": "prod-2", "quantity_pieces": 100.0},
        {"product_id": "prod-3", "quantity_pieces": 50.0},
    ]

    customers = [
        {"id": "cust-1", "name": "أحمد علي", "phone": "01012345678", "address": "القاهرة - المعادي", "points": 120, "balance": 0.0}
    ]

    db.sync_catalog(categories, products, stocks, customers)
    print("Local database seeded successfully with EGP currency!")

if __name__ == "__main__":
    seed()
