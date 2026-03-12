using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System.Globalization;

namespace WebApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class SalesController : ControllerBase
    {
        private readonly ILogger<SalesController> _logger;

        public SalesController(ILogger<SalesController> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Returns a deterministic sales summary for a given date.
        /// </summary>
        /// <param name="date">Date in YYYY-MM-DD format.</param>
        /// <returns>Sales amount for the given date.</returns>
        [HttpGet("summary")]
        public IActionResult GetSalesSummary([FromQuery] string date)
        {
            _logger.LogInformation("Received sales summary request for date={Date}", date);

            if (string.IsNullOrWhiteSpace(date))
            {
                _logger.LogWarning("Missing required 'date' query parameter.");
                return BadRequest(new { error = "Query parameter 'date' is required in YYYY-MM-DD format." });
            }

            if (!DateTime.TryParse(date, out var parsedDate))
            {
                _logger.LogWarning("Invalid date format received: {Date}", date);
                return BadRequest(new { error = "Invalid date format. Use YYYY-MM-DD." });
            }

            string normalizedDate = parsedDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

            int year = parsedDate.Year;
            int month = parsedDate.Month;
            int day = parsedDate.Day;

            double amount = ((year * month * day) % 5000) + 500;

            _logger.LogInformation("Sales summary for {Date}: {Amount}", normalizedDate, amount);

            return Ok(new
            {
                date = normalizedDate,
                amount
            });
        }
    }
}
