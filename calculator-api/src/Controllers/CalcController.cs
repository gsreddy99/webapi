using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace WebApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class CalcController : ControllerBase
    {
        private readonly ILogger<CalcController> _logger;

        public CalcController(ILogger<CalcController> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Performs a basic arithmetic operation.
        /// </summary>
        /// <param name="a">First operand.</param>
        /// <param name="b">Second operand.</param>
        /// <param name="op">Operation: add, subtract, multiply, divide.</param>
        /// <returns>JSON result or error.</returns>
        [HttpGet]
        public IActionResult Calculate(
            [FromQuery] double a,
            [FromQuery] double b,
            [FromQuery] string op)
        {
            _logger.LogInformation("Calculate called with a={A}, b={B}, op={Op}", a, b, op);

            if (string.IsNullOrWhiteSpace(op))
            {
                _logger.LogWarning("Operator missing.");
                return BadRequest(new { error = "Operator is required. Use add, subtract, multiply, or divide." });
            }

            double result;

            switch (op.ToLowerInvariant())
            {
                case "add":
                    result = a + b;
                    break;

                case "subtract":
                    result = a - b;
                    break;

                case "multiply":
                    result = a * b;
                    break;

                case "divide":
                    if (b == 0)
                    {
                        _logger.LogWarning("Division by zero attempt: a={A}, b={B}", a, b);
                        return BadRequest(new { error = "Division by zero is not allowed." });
                    }
                    result = a / b;
                    break;

                default:
                    _logger.LogWarning("Invalid operator received: {Op}", op);
                    return BadRequest(new { error = "Invalid operator. Use add, subtract, multiply, or divide." });
            }

            return Ok(new { result });
        }
    }
}
