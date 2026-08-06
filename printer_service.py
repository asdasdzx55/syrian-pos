import datetime

class ThermalPrinter80mm:
    """
    Xprinter 80mm ESC/POS Professional Thermal Receipt Generator for Al-Manzil Al-Souri Market.
    Width: 48 characters per line.
    Supports dynamic store header, drawn table grid, X & Z shift reports, and shelf barcode label printing.
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

    def generate_x_report_text(self, x_data):
        info = self.get_store_info()
        lines = []
        lines.append("╔" + "═" * 46 + "╗")
        lines.append("║" + info["name"].center(46) + "║")
        lines.append("║" + "🔍 [ تقرير X ] - تفتيش الوردية الحالية".center(46) + "║")
        lines.append("╠" + "═" * 46 + "╣")
        lines.append(f"║ الكاشير: {x_data['cashier_name']}".ljust(47) + "║")
        lines.append(f"║ وقت بداية الوردية: {x_data['start_time']}".ljust(47) + "║")
        lines.append(f"║ وقت المعاينة الحالي: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(47) + "║")
        lines.append("╠" + "─" * 46 + "╣")
        lines.append(f"║ عدد الفواتير المنفذة: {x_data['invoice_count']} فاتورة".ljust(47) + "║")
        lines.append(f"║ الرصيد الافتتاحي للدرج: {x_data['opening_cash']:.2f} ج.م".ljust(47) + "║")
        lines.append(f"║ إجمالي مبيعات الكاش (نقداً): {x_data['cash_sales']:.2f} ج.م".ljust(47) + "║")
        lines.append(f"║ إجمالي مبيعات البطاقات/فيزا: {x_data['card_sales']:.2f} ج.م".ljust(47) + "║")
        lines.append(f"║ إجمالي مبيعات انستا باي: {x_data['instapay_sales']:.2f} ج.م".ljust(47) + "║")
        lines.append(f"║ إجمالي مبيعات فودافون كاش: {x_data['vodafone_sales']:.2f} ج.م".ljust(47) + "║")
        lines.append(f"║ إجمالي الخصومات الممنوحة: -{x_data['total_discounts']:.2f} ج.م".ljust(47) + "║")
        lines.append("╠" + "═" * 46 + "╣")
        lines.append(f"║ 💰 إجمالي مبيعات الوردية: {x_data['total_sales']:.2f} ج.م".ljust(47) + "║")
        lines.append(f"║ 💵 النقدية المتوقعة حالياً بالدرج: {x_data['expected_cash']:.2f} ج.م".ljust(47) + "║")
        lines.append("╚" + "═" * 46 + "╝")
        return "\n".join(lines)

    def generate_z_report_text(self, z_data):
        info = self.get_store_info()
        lines = []
        lines.append("╔" + "═" * 46 + "╗")
        lines.append("║" + info["name"].center(46) + "║")
        lines.append("║" + "🔴 [ تقرير Z ] - إقفال وتصفير الوردية النهائي".center(46) + "║")
        lines.append("╠" + "═" * 46 + "╣")
        lines.append(f"║ الكاشير: {z_data['cashier_name']}".ljust(47) + "║")
        lines.append(f"║ وقت بداية الوردية: {z_data['start_time']}".ljust(47) + "║")
        lines.append(f"║ وقت الإقفال والتصفير: {z_data['end_time']}".ljust(47) + "║")
        lines.append("╠" + "─" * 46 + "╣")
        lines.append(f"║ عدد الفواتير الإجمالي: {z_data['invoice_count']} فاتورة".ljust(47) + "║")
        lines.append(f"║ إجمالي المبيعات الكلية: {z_data['total_sales']:.2f} ج.م".ljust(47) + "║")
        lines.append(f"║ النقدية الكاش بالدرج (متوقع): {z_data['expected_cash']:.2f} ج.م".ljust(47) + "║")
        lines.append(f"║ النقدية الفعلية بعد العد: {z_data['actual_cash']:.2f} ج.م".ljust(47) + "║")

        var = z_data['variance']
        var_text = f"عجز بالدرج: {var:.2f} ج.م ⚠️" if var < 0 else f"زيادة بالدرج: +{var:.2f} ج.م 🎉" if var > 0 else "مطابقة تامة 100% 🎯"
        lines.append(f"║ فروقات الدرج: {var_text}".ljust(47) + "║")
        lines.append("╠" + "═" * 46 + "╣")
        lines.append(f"║ 🌟 رصيد الدرج الافتتاحي للوردية القادمة: {z_data['next_opening_cash']:.2f} ج.م".ljust(47) + "║")
        lines.append("║ " + "تم حسم وإقفال الوردية وتصفير المبيعات بنجاح!".center(44) + " ║")
        lines.append("╚" + "═" * 46 + "╝")
        return "\n".join(lines)

    def generate_barcode_label_text(self, product_name, price, barcode, scale_code="", category=""):
        info = self.get_store_info()
        lines = []
        lines.append("┌" + "─" * 38 + "┐")
        lines.append("│" + info["name"].center(38) + "│")
        lines.append("├" + "─" * 38 + "┤")
        lines.append("│ " + f"{product_name[:26]:<26}".rjust(36) + " │")
        if category:
            lines.append("│ " + f"القسم: {category[:20]}".rjust(36) + " │")
        if scale_code:
            lines.append("│ " + f"كود الميزان الـ 5 أرقام: {scale_code}".rjust(36) + " │")
        lines.append("├" + "─" * 38 + "┤")
        lines.append("│ " + f"السعر: {price:.2f} ج.م (EGP)".center(36) + " │")
        lines.append("│ " + f"|||| ||| ||||| {barcode or scale_code} |||| |||".center(36) + " │")
        lines.append("└" + "─" * 38 + "┘")
        return "\n".join(lines)
