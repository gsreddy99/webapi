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
            double result = op switch
            {
                "add" => a + b,
                "subtract" => a - b,
                "multiply" => a * b,
                "divide" => b != 0 ? a / b : double.NaN,
                _ => double.NaN
            };

            return Ok(new { result });
        }
    }
}
