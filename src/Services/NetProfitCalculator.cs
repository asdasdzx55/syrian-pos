using System;
using System.Collections.Generic;
using System.Linq;
using AlmanzilSouriPos.Models;

namespace AlmanzilSouriPos.Services
{
    public class NetProfitReport
    {
        public DateTime StartDate { get; set; }
        public DateTime EndDate { get; set; }
        public decimal TotalSales { get; set; }
        public decimal CostOfGoodsSold { get; set; }
        public decimal TotalOperatingExpenses { get; set; }
        public decimal TotalPartnerWithdrawals { get; set; }
        public decimal TotalSalaries { get; set; }
        public decimal NetProfit { get; set; }
    }

    public static class NetProfitCalculator
    {
        /// <summary>
        /// Calculates Net Profit engine formula: NetProfit = TotalSales - (COGS + OperatingExpenses + Salaries)
        /// Partner withdrawals are isolated and not treated as operational expenses.
        /// </summary>
        public static NetProfitReport Calculate(
            IEnumerable<Invoice> invoices,
            IEnumerable<InvoiceItem> invoiceItems,
            IEnumerable<Product> products,
            IEnumerable<Expense> expenses,
            IEnumerable<HrRecord> hrRecords,
            DateTime startDate,
            DateTime endDate)
        {
            var filteredInvoices = invoices.Where(i => i.CreatedAt >= startDate && i.CreatedAt <= endDate && i.Status == "completed").ToList();
            var filteredInvIds = filteredInvoices.Select(i => i.Id).ToHashSet();

            decimal totalSales = filteredInvoices.Sum(i => i.NetTotal);

            // Calculate COGS
            var productCostDict = products.ToDictionary(p => p.Id, p => p.PieceCost);
            var filteredItems = invoiceItems.Where(item => filteredInvIds.Contains(item.InvoiceId));

            decimal cogs = 0.0m;
            foreach (var item in filteredItems)
            {
                decimal pieceCost = productCostDict.TryGetValue(item.ProductId, out var cost) ? cost : 0.0m;
                decimal piecesCount = item.Quantity;
                if (item.UnitSold == "carton")
                {
                    piecesCount *= item.UnitsPerCarton;
                }
                cogs += piecesCount * pieceCost;
            }

            // Filter Expenses (Operating vs Partner Withdrawals)
            var filteredExpenses = expenses.Where(e => e.CreatedAt >= startDate && e.CreatedAt <= endDate).ToList();
            decimal operatingExpenses = filteredExpenses.Where(e => e.Type == "operating").Sum(e => e.Amount);
            decimal partnerWithdrawals = filteredExpenses.Where(e => e.Type == "partner_withdrawal").Sum(e => e.Amount);

            // Filter Salaries
            var filteredHr = hrRecords.Where(h => h.CreatedAt >= startDate && h.CreatedAt <= endDate).ToList();
            decimal totalSalaries = filteredHr.Sum(h => h.Amount);

            decimal netProfit = totalSales - (cogs + operatingExpenses + totalSalaries);

            return new NetProfitReport
            {
                StartDate = startDate,
                EndDate = endDate,
                TotalSales = totalSales,
                CostOfGoodsSold = cogs,
                TotalOperatingExpenses = operatingExpenses,
                TotalPartnerWithdrawals = partnerWithdrawals,
                TotalSalaries = totalSalaries,
                NetProfit = netProfit
            };
        }
    }
}
