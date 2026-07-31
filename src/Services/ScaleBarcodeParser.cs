using System;

namespace AlmanzilSouriPos.Services
{
    public class ScaleBarcodeResult
    {
        public bool IsScaleBarcode { get; set; }
        public string ItemCode { get; set; } = string.Empty;
        public decimal WeightKg { get; set; }
        public decimal PriceValue { get; set; }
        public bool IsWeightBased { get; set; }
    }

    public static class ScaleBarcodeParser
    {
        /// <summary>
        /// Parses 13-digit scale barcodes (EAN-13 format) starting with '20' or '21'.
        /// Structure: PP [5-digit Item Code] [5-digit Weight in Grams or Price] C
        /// Example: 2000105012503 => Prefix '20', Item '00105', Weight '01250'g = 1.250kg
        /// </summary>
        public static ScaleBarcodeResult Parse(string barcode)
        {
            var result = new ScaleBarcodeResult();

            if (string.IsNullOrWhiteSpace(barcode) || barcode.Length != 13)
            {
                result.IsScaleBarcode = false;
                return result;
            }

            string prefix = barcode.Substring(0, 2);
            if (prefix == "20" || prefix == "21")
            {
                result.IsScaleBarcode = true;
                result.ItemCode = barcode.Substring(2, 5);
                
                string valueSegment = barcode.Substring(7, 5);
                if (decimal.TryParse(valueSegment, out decimal parsedVal))
                {
                    if (prefix == "20")
                    {
                        // Weight in grams (e.g. 01250 -> 1.250 kg)
                        result.IsWeightBased = true;
                        result.WeightKg = parsedVal / 1000.0m;
                    }
                    else
                    {
                        // Price based in currency units (e.g. 01500 -> 15.00)
                        result.IsWeightBased = false;
                        result.PriceValue = parsedVal / 100.0m;
                    }
                }
            }

            return result;
        }
    }
}
