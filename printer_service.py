import datetime

class ThermalPrinter80mm:
    """
    Xprinter 80mm ESC/POS Professional Thermal Receipt Generator for Al-Manzil Al-Souri Market.
    Width: 48 characters per line.
    Supports dynamic store header, drawn table grid, and store settings from database.
    """
    LINE_WIDTH = 48

    def __init__(self, db=None):
        self.db = db

    def get_store_info(self):
        if self.db:
            return {
                "name": self.db.get_setting("store_name", "سوبرماركت المنزل السوري"),
                "phone": self.db.get_setting("store_phone", "01277695799 / 01099887766"),
                "address": self.db.get_setting("store_address", "القاهرة / الجيزة - مصر"),
                "tax_id": self.db.get_setting("store_tax_id", "س.ت: 109842 | ب.ض: 450-891-230")
            }
        return {
            "name": "سوبرماركت المنزل السوري",
            "phone": "01277695799 / 01099887766",
            "address": "القاهرة / الجيزة - مصر",
            "tax_id": "س.ت: 109842 | ب.ض: 450-891-230"
        }

    def generate_receipt_text(self, invoice_number, items, subtotal, discount=0.0, net_total=None, payment_method="نقداً (ج.م)", customer_name="عميل نقدي", customer_phone="", delivery_address=""):
        info = self.get_store_info()
        if net_total is None:
            net_total = max(0.0, subtotal - discount)

        lines = []
        lines.append("╔" + "═" * 46 + "╗")
        lines.append("║" + info["name"].center(46) + "║")
        lines.append("║" + info["tax_id"].center(46) + "║")
        lines.append("║" + f"العنوان: {info['address']}".center(46) + "║")
        lines.append("║" + f"الهاتف: {info['phone']}".center(46) + "║")
        lines.append("╠" + "═" * 46 + "╣")
        lines.append(f"║ رقم الفاتورة: #{invoice_number}".ljust(47) + "║")
        lines.append(f"║ التاريخ والوقت: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(47) + "║")
        lines.append(f"║ العميل: {customer_name}".ljust(47) + "║")
        if customer_phone:
            lines.append(f"║ الهاتف: {customer_phone}".ljust(47) + "║")
        if delivery_address:
            lines.append(f"║ العنوان: {delivery_address}".ljust(47) + "║")
        lines.append(f"║ طريقة الدفع: {payment_method}".ljust(47) + "║")
        lines.append("╠" + "═" * 46 + "╣")
        
        # Professional Drawn Table Header
        lines.append("║ " + f"{'الصنف':<18} {'القطع/الوزن':<11} {'السعر':<7} {'الإجمالي':<7}" + " ║")
        lines.append("╠" + "─" * 46 + "╣")

        for idx, item in enumerate(items, 1):
            name_txt = item['name'][:18]
            pieces = int(item.get("piece_qty", item.get("quantity", 1)))
            weight_g = float(item.get("weight_grams", 1000))
            weight_str = f"{weight_g:.0f}ج" if weight_g < 1000 else f"{(weight_g/1000):.1f}كج"
            qty_weight_str = f"{pieces}ق ({weight_str})"
            price_txt = f"{item['unit_price']:.1f}"
            tot_txt = f"{item['total_price']:.1f}"

            lines.append("║ " + f"{name_txt:<18} {qty_weight_str:<11} {price_txt:>7} {tot_txt:>7}" + " ║")

        lines.append("╠" + "═" * 46 + "╣")
        lines.append("║ " + f"المجموع الفرعي: {subtotal:.2f} ج.م".rjust(44) + " ║")
        if discount > 0:
            lines.append("║ " + f"الخصم المباشر: -{discount:.2f} ج.م".rjust(44) + " ║")
        lines.append("║ " + f"الصافي المطلوب: {net_total:.2f} ج.م".rjust(44) + " ║")
        lines.append("╠" + "─" * 46 + "╣")
        lines.append("║ " + f"⭐️ نقاط الولاء المكتسبة: {int(net_total / 10)} نقطة".center(44) + " ║")
        lines.append("║ " + "||| | |||| | ||||| | ||| | ||||".center(44) + " ║")
        lines.append("║ " + f"شكراً لتسوقكم من {info['name']} 🇸🇾".center(44) + " ║")
        lines.append("║ " + "أهلاً وسهلاً بكم دائماً!".center(44) + " ║")
        lines.append("╚" + "═" * 46 + "╝")

        return "\n".join(lines)
