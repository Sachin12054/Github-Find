// =============================================================================
// UserService.cs — Sample C# file with INTENTIONAL issues for testing
// =============================================================================
// This file contains deliberate code quality issues to demonstrate the
// AI reviewer's detection capabilities.
// =============================================================================

using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.Linq;
using System.Threading.Tasks;

namespace SampleApp.Services
{
    public class UserService
    {
        // ISSUE: Hardcoded connection string (Security)
        private string connectionString = "Server=prod-db;Database=Users;User=admin;Password=P@ssw0rd123;";

        // ISSUE: No interface / no dependency injection (SOLID - Dependency Inversion)
        private SqlConnection _connection;

        public UserService()
        {
            // ISSUE: Creating concrete dependency in constructor (SOLID - DIP)
            _connection = new SqlConnection(connectionString);
        }

        // ISSUE: async method without await (Async/Await mistake)
        public async Task<User> GetUserById(int id)
        {
            var user = FindUser(id);
            return user;
        }

        // ISSUE: SQL Injection vulnerability (Security)
        public User FindUserByName(string name)
        {
            var query = "SELECT * FROM Users WHERE Name = '" + name + "'";
            // Execute query...
            return new User();
        }

        // ISSUE: No null check on parameter (Null Reference)
        public string GetUserEmail(User user)
        {
            return user.Email.ToLower();
        }

        // ISSUE: Empty catch block - swallowing exceptions (Exception Handling)
        public void SaveUser(User user)
        {
            try
            {
                // Save logic
                _connection.Open();
            }
            catch (Exception)
            {
                // silently swallowed
            }
        }

        // ISSUE: String concatenation in loop (Performance)
        public string GenerateReport(List<User> users)
        {
            string report = "";
            foreach (var user in users)
            {
                report += "User: " + user.Name + ", Email: " + user.Email + "\n";
            }
            return report;
        }

        // ISSUE: Method does too many things (SOLID - SRP)
        public void ProcessUserRegistration(string name, string email, string password)
        {
            // Validate
            if (name.Length < 2) throw new Exception("Bad name");

            // Hash password
            var hash = password.GetHashCode().ToString();

            // Save to DB
            var query = $"INSERT INTO Users VALUES ('{name}', '{email}', '{hash}')";

            // Send welcome email
            Console.WriteLine($"Sending email to {email}");

            // Log
            Console.WriteLine($"User {name} registered");
        }

        // ISSUE: Using .Result (sync-over-async)
        public User GetUserSync(int id)
        {
            var user = GetUserById(id).Result;
            return user;
        }

        private User FindUser(int id)
        {
            return new User { Id = id, Name = "Test", Email = "test@test.com" };
        }
    }

    public class User
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
    }
}
