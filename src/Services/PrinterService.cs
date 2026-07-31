using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using AlmanzilSouriPos.Models;

namespace AlmanzilSouriPos.Services
{
    public class PrinterService
    {
        private const int MaxLineWidth = 48; // Standard 80mm Thermal Printer Width (48 chars per line)

        public string StoreName { get; set; } = "سوبرماركت المنزل السوري";
        public string StoreAddress { get; set; } = "العنوان: دمشق / القاهرة - فرع المنزل السوري";
        public string StorePhone { get; set; } = "هاتف: 01012345678 - 01198765432";
        public string WebsiteUrl { get; set; } = "الموقع: www.almanzilsouri.com";

        /// <summary>
        /// Generates ESC/POS byte sequence for Xprinter 80mm thermal receipt.
        /// </summary>
        public byte[] GenerateEscPosReceiptBytes(Invoice invoice)
        {
            using (var ms = new MemoryStream())
            using (var writer = new BinaryWriter(ms, Encoding.UTF8))
            {
                // Initialize Printer (ESC @)
                writer.Write(new byte[] { 0x1B, 0x40 });

                // Center Align (ESC a 1)
                writer.Write(new byte[] { 0x1B, 0x61, 0x01 });

                // Double height & double width font for Title (ESC ! 0x30)
                writer.Write(new byte[] { 0x1B, 0x21, 0x30 });
                WriteString(writer, StoreName + "\n");

                // Reset font size (ESC ! 0x00)
                writer.Write(new byte[] { 0x1B, 0x21, 0x00 });
                WriteString(writer, StoreAddress + "\n");
                WriteString(writer, StorePhone + "\n");
                WriteString(writer, WebsiteUrl + "\n");
                WriteString(writer, new string('-', MaxLineWidth) + "\n");

                // Left Align (ESC a 0)
                writer.Write(new byte[] { 0x1B, 0x61, 0x00 });
                WriteString(writer, $"فاتورة رقم: {invoice.InvoiceNumber}\n");
                WriteString(writer, $"التاريخ: {invoice.CreatedAt:yyyy-MM-dd HH:mm:ss}\n");
                WriteString(writer, $"العميل: {invoice.CustomerName}\n");
                if (!string.IsNullOrWhiteSpace(invoice.CustomerPhone))
                {
                    WriteString(writer, $"الهاتف: {invoice.CustomerPhone}\n");
                }
                if (!string.IsNullOrWhiteSpace(invoice.DeliveryAddress))
                {
                    WriteString(writer, $"عنوان التوصيل: {invoice.DeliveryAddress}\n");
                }
                WriteString(writer, $"طريقة الدفع: {GetPaymentMethodText(invoice.PaymentMethod)}\n");
                WriteString(writer, new string('=', MaxLineWidth) + "\n");

                // Header Table Line
                WriteString(writer, FormatRow("المنتج", "العدد", "السعر", "الإجمالي") + "\n");
                WriteString(writer, new string('-', MaxLineWidth) + "\n");

                // Invoice Items
                foreach (var item in invoice.Items)
                {
                    string unitStr = item.UnitSold == "piece" ? "قطعة" : (item.UnitSold == "carton" ? "كرتونة" : "كجم");
                    string nameText = $"{item.ProductName} ({unitStr})";
                    string qtyText = item.Quantity.ToString("0.##");
                    string priceText = item.UnitPrice.ToString("0.00");
                    string totalText = item.TotalPrice.ToString("0.00");

                    WriteString(writer, FormatRow(nameText, qtyText, priceText, totalText) + "\n");
                }

                WriteString(writer, new string('=', MaxLineWidth) + "\n");

                // Right Align for Totals
                writer.Write(new byte[] { 0x1B, 0x61, 0x02 });
                WriteString(writer, $"المجموع الفرعي: {invoice.Subtotal:0.00} ل.س\n");
                if (invoice.Discount > 0)
                {
                    WriteString(writer, $"الخصم: -{invoice.Discount:0.00} ل.س\n");
                }
                if (invoice.DeliveryCharge > 0)
                {
                    WriteString(writer, $"خدمة التوصيل: {invoice.DeliveryCharge:0.00} ل.س\n");
                }

                // Bold & Large Font for Net Total
                writer.Write(new byte[] { 0x1B, 0x21, 0x20 });
                WriteString(writer, $"الإجمالي النهائي: {invoice.NetTotal:0.00} ل.س\n");

                // Center Align Footer
                writer.Write(new byte[] { 0x1B, 0x21, 0x00 });
                writer.Write(new byte[] { 0x1B, 0x61, 0x01 });
                WriteString(writer, new string('-', MaxLineWidth) + "\n");
                WriteString(writer, "شكراً لتسوقكم من المنزل السوري!\n");
                WriteString(writer, "أهلاً وسهلاً بكم دائماً\n\n\n");

                // Cut Paper Command (GS V 0)
                writer.Write(new byte[] { 0x1D, 0x56, 0x00 });

                return ms.ToArray();
            }
        }

        private string GetPaymentMethodText(string method)
        {
            return method switch
            {
                "cash" => "نقداً (Cash)",
                "visa" => "فيزا (Visa)",
                "instapay" => "انستا باي (InstaPay)",
                "vodafone_cash" => "فودافون كاش (Vodafone Cash)",
                "split" => "دفع متعدد (Split)",
                _ => "نقداً"
            };
        }

        private string FormatRow(string name, string qty, string price, string total)
        {
            // Pad columns to fit 48 characters width nicely
            name = name.Length > 20 ? name.Substring(0, 17) + "..." : name;
            return string.Format("{0,-20} {1,6} {2,9} {3,10}", name, qty, price, total);
        }

        private void WriteString(BinaryWriter writer, string text)
        {
            byte[] bytes = Encoding.UTF8.GetBytes(text);
            writer.Write(bytes);
        }
    }
}
