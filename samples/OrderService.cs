// =============================================================================
// OrderService.cs — Another sample C# file with issues for testing
// =============================================================================

using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SampleApp.Services
{
    public class OrderService
    {
        private readonly UserService _userService;

        public OrderService()
        {
            // ISSUE: Tight coupling, no DI (SOLID)
            _userService = new UserService();
        }

        // ISSUE: async without await
        public async Task<Order> CreateOrder(int userId, List<OrderItem> items)
        {
            var order = new Order
            {
                UserId = userId,
                Items = items,
                Total = CalculateTotal(items),
                CreatedAt = DateTime.Now  // ISSUE: Should use DateTime.UtcNow
            };

            return order;
        }

        // ISSUE: No input validation, no null check
        public decimal CalculateTotal(List<OrderItem> items)
        {
            decimal total = 0;
            foreach (var item in items)
            {
                total += item.Price * item.Quantity;
            }
            // ISSUE: Magic number
            if (total > 100)
            {
                total *= 0.9m; // 10% discount — magic number
            }
            return total;
        }

        // ISSUE: Catching generic Exception, throwing generic Exception
        public void CancelOrder(int orderId)
        {
            try
            {
                // Cancel logic
                if (orderId <= 0)
                    throw new Exception("Invalid order ID");
            }
            catch (Exception ex)
            {
                throw new Exception("Failed to cancel order", ex);
            }
        }

        // ISSUE: No disposal of resources, no using statement
        public async Task ExportOrders()
        {
            var file = System.IO.File.OpenWrite("orders.csv");
            // Write data...
            // ISSUE: file stream never closed/disposed
        }
    }

    public class Order
    {
        public int Id { get; set; }
        public int UserId { get; set; }
        public List<OrderItem> Items { get; set; }
        public decimal Total { get; set; }
        public DateTime CreatedAt { get; set; }
    }

    public class OrderItem
    {
        public string ProductName { get; set; }
        public decimal Price { get; set; }
        public int Quantity { get; set; }
    }
}
