// =============================================================================
// UserService.cs — Clean sample C# service for AI review demos
// =============================================================================
// =============================================================================

using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SampleApp.Services
{
    public class UserService
    {
        private const int MinNameLength = 2;

        private SqlConnection _connection;

        public UserService()
        {
            var connectionString = Environment.GetEnvironmentVariable("USER_DB_CONNECTION_STRING");
            if (string.IsNullOrWhiteSpace(connectionString))
            {
                throw new InvalidOperationException("USER_DB_CONNECTION_STRING is not configured.");
            }

            _connection = new SqlConnection(connectionString);
        }

        public async Task<User> GetUserById(int id)
        {
            await Task.Yield();
            return FindUser(id);
        }

        public User FindUserByName(string name)
        {
            if (string.IsNullOrWhiteSpace(name))
            {
                throw new ArgumentException("Name is required.", nameof(name));
            }

            using var command = new SqlCommand("SELECT * FROM Users WHERE Name = @name", _connection);
            command.Parameters.AddWithValue("@name", name);
            // Execute query...
            return new User();
        }

        public string GetUserEmail(User user)
        {
            if (user is null)
            {
                throw new ArgumentNullException(nameof(user));
            }

            return user.Email.ToLower();
        }

        public void SaveUser(User user)
        {
            try
            {
                // Save logic
                _connection.Open();
            }
            catch (SqlException ex)
            {
                Console.Error.WriteLine(ex);
                throw;
            }
        }

        public string GenerateReport(List<User> users)
        {
            var reportBuilder = new StringBuilder();
            foreach (var user in users)
            {
                reportBuilder.AppendLine($"User: {user.Name}, Email: {user.Email}");
            }
            return reportBuilder.ToString();
        }

        public void ProcessUserRegistration(string name, string email, string password)
        {
            if (string.IsNullOrWhiteSpace(name) || name.Length < MinNameLength)
            {
                throw new ArgumentException("Bad name", nameof(name));
            }

            var hash = password.GetHashCode().ToString();

            using var command = new SqlCommand("INSERT INTO Users (Name, Email, PasswordHash) VALUES (@name, @email, @hash)", _connection);
            command.Parameters.AddWithValue("@name", name);
            command.Parameters.AddWithValue("@email", email);
            command.Parameters.AddWithValue("@hash", hash);

            Console.WriteLine($"Sending email to {email}");
            Console.WriteLine($"User {name} registered");
        }

        public async Task<User> GetUserByIdAsync(int id)
        {
            return await GetUserById(id);
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
