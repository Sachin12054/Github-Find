// =============================================================================
// OrderService.cs — Clean sample C# order workflow for AI review demos
// =============================================================================

using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SampleApp.Services
{
    public class OrderService
    {
        private readonly UserService _userService;
        private const decimal DiscountThreshold = 100m;
        private const decimal DiscountRate = 0.9m;

        public OrderService(UserService userService)
        {
            _userService = userService ?? throw new ArgumentNullException(nameof(userService));
        }

        public async Task<Order> CreateOrder(int userId, List<OrderItem> items)
        {
            if (items is null || items.Count == 0)
            {
                throw new ArgumentException("At least one order item is required.", nameof(items));
            }

            var user = await _userService.GetUserByIdAsync(userId);
            if (user is null)
            {
                throw new InvalidOperationException($"User {userId} was not found.");
            }

            await Task.Yield();

            var order = new Order
            {
                UserId = userId,
                Items = items,
                Total = CalculateTotal(items),
                CreatedAt = DateTime.UtcNow
            };

            return order;
        }

        public decimal CalculateTotal(List<OrderItem> items)
        {
            if (items is null)
            {
                throw new ArgumentNullException(nameof(items));
            }

            decimal total = 0;
            foreach (var item in items)
            {
                if (item is null)
                {
                    throw new ArgumentException("Order items cannot contain null entries.", nameof(items));
                }

                total += item.Price * item.Quantity;
            }
            if (total > DiscountThreshold)
            {
                total *= DiscountRate;
            }
            return total;
        }

        public void CancelOrder(int orderId)
        {
            if (orderId <= 0)
            {
                throw new ArgumentOutOfRangeException(nameof(orderId), "Invalid order ID");
            }

            // Cancel logic
        }

        public async Task ExportOrders()
        {
            using var file = System.IO.File.OpenWrite("orders.csv");
            // Write data...
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
