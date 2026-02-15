using Microsoft.AspNetCore.Mvc;

namespace WebApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class CalcController : ControllerBase
    {
        [HttpGet]
        public IActionResult Calculate(double a, double b, string op)
        {
            if (op == "divide" && b == 0)
                return BadRequest(new { error = "Division by zero is not allowed." });

            double result = op switch
            {
                "add" => a + b,
                "subtract" => a - b,
                "multiply" => a * b,
                "divide" => a / b,
                _ => throw new ArgumentException("Invalid operator")
            };

            return Ok(new { result });

        }
    }
}
