using System;
using System.Collections.Generic;

namespace AlmanzilSouriPos.Models
{
    public class Product
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string? CategoryId { get; set; }
        public string Name { get; set; } = string.Empty;
        public string UnitType { get; set; } = "pcs"; // 'pcs' or 'kg'
        public bool HasMultiUnit { get; set; }
        public string? PieceBarcode { get; set; }
        public string? CartonBarcode { get; set; }
        public int UnitsPerCarton { get; set; } = 1;
        public decimal PiecePrice { get; set; }
        public decimal PieceCost { get; set; }
        public decimal CartonPrice { get; set; }
        public decimal CartonCost { get; set; }
        public decimal MinStockAlert { get; set; } = 5;
        public decimal StockQty { get; set; }
        public bool IsActive { get; set; } = true;
    }

    public class Customer
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Name { get; set; } = string.Empty;
        public string Phone { get; set; } = string.Empty;
        public string Address { get; set; } = string.Empty;
        public int Points { get; set; }
        public decimal Balance { get; set; }
    }

    public class InvoiceItem
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string InvoiceId { get; set; } = string.Empty;
        public string ProductId { get; set; } = string.Empty;
        public string ProductName { get; set; } = string.Empty;
        public string UnitSold { get; set; } = "piece"; // piece, carton, kg
        public int UnitsPerCarton { get; set; } = 1;
        public decimal Quantity { get; set; } = 1;
        public decimal UnitPrice { get; set; }
        public decimal TotalPrice { get; set; }
    }

    public class Invoice
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string InvoiceNumber { get; set; } = string.Empty;
        public string? CustomerId { get; set; }
        public string CustomerName { get; set; } = "عميل نقدي";
        public string CustomerPhone { get; set; } = string.Empty;
        public string DeliveryAddress { get; set; } = string.Empty;
        public string SaleType { get; set; } = "in_store"; // in_store, delivery
        public string PaymentMethod { get; set; } = "cash"; // cash, visa, instapay, vodafone_cash, split
        public decimal Subtotal { get; set; }
        public decimal Tax { get; set; }
        public decimal Discount { get; set; }
        public decimal DeliveryCharge { get; set; }
        public decimal NetTotal { get; set; }
        public string Status { get; set; } = "completed"; // completed, returned, held
        public bool IsSynced { get; set; }
        public DateTime CreatedAt { get; set; } = DateTime.Now;

        public List<InvoiceItem> Items { get; set; } = new List<InvoiceItem>();
    }

    public class Supplier
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Name { get; set; } = string.Empty;
        public string Company { get; set; } = string.Empty;
        public string Phone { get; set; } = string.Empty;
        public string Address { get; set; } = string.Empty;
        public decimal CurrentBalance { get; set; }
    }

    public class SupplierTransaction
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string SupplierId { get; set; } = string.Empty;
        public string Type { get; set; } = "purchase"; // purchase, payment
        public decimal Amount { get; set; }
        public string Description { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; } = DateTime.Now;
    }

    public class Employee
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Name { get; set; } = string.Empty;
        public string Role { get; set; } = "cashier";
        public string Phone { get; set; } = string.Empty;
        public decimal BaseSalary { get; set; }
        public bool IsActive { get; set; } = true;
    }

    public class HrRecord
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string EmployeeId { get; set; } = string.Empty;
        public string Type { get; set; } = "salary_payment"; // salary_payment, advance, bonus, deduction
        public decimal Amount { get; set; }
        public string Description { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; } = DateTime.Now;
    }

    public class Expense
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Type { get; set; } = "operating"; // operating, partner_withdrawal
        public decimal Amount { get; set; }
        public string Description { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; } = DateTime.Now;
    }
}
