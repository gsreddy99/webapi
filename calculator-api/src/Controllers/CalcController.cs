using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace WebApi.Controllers
{

    [ApiController]
    [Route("health")]
    public class HealthController : ControllerBase
    {
    [HttpGet]
    public IActionResult Get() => Ok("healthy");
    }


    [ApiController]
    [Route("api/[controller]")]
    public class CalcController : ControllerBase
    {
        private readonly ILogger<CalcController> _logger;

        public CalcController(ILogger<CalcController> logger)
        {
            _logger = logger;
        }

        [HttpGet]
        public IActionResult Calculate(double a, double b, string op)
        {
            _logger.LogInformation("Received request: a={A}, b={B}, op={Op}", a, b, op);

            // Validate operator
            if (op is not ("add" or "subtract" or "multiply" or "divide"))
            {
                _logger.LogWarning("Invalid operator received: {Op}", op);
                return BadRequest(new { error = "Invalid operator. Use add, subtract, multiply, or divide." });
            }

            // Handle divide by zero
            if (op == "divide" && b == 0)
            {
                _logger.LogWarning("Division by zero attempted: a={A}, b={B}", a, b);
                return BadRequest(new { error = "Division by zero is not allowed." });
            }

            double result = op switch
            {
                "add" => a + b,
                "subtract" => a - b,
                "multiply" => a * b,
                "divide" => a / b,
                _ => 0 // unreachable because we validated above
            };

            _logger.LogInformation("Calculated result: {Result}", result);

            return Ok(new { result });
        }
    }
}
