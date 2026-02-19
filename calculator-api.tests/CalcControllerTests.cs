using System;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using WebApi.Controllers;
using Xunit;
using Moq;

namespace calculator_api.tests
{
    public class CalcControllerTests
    {
        private readonly CalcController _controller;
        private readonly Mock<ILogger<CalcController>> _loggerMock;

        public CalcControllerTests()
        {
            _loggerMock = new Mock<ILogger<CalcController>>();
            _controller = new CalcController(_loggerMock.Object);
        }

        [Fact]
        public void Calculate_Addition_ReturnsCorrectResult()
        {
            // Arrange
            double a = 5;
            double b = 3;
            string op = "add";

            // Act
            var result = _controller.Calculate(a, b, op) as OkObjectResult;

            // Assert
            Assert.NotNull(result);
            Assert.Equal(200, result.StatusCode);

            // Access the result property directly
            var response = result.Value;
            Assert.Equal(8.0, response.GetType().GetProperty("result").GetValue(response));
        }

        [Fact]
        public void Calculate_Subtraction_ReturnsCorrectResult()
        {
            // Arrange
            double a = 10;
            double b = 4;
            string op = "subtract";

            // Act
            var result = _controller.Calculate(a, b, op) as OkObjectResult;

            // Assert
            Assert.NotNull(result);
            Assert.Equal(200, result.StatusCode);

            var response = result.Value;
            Assert.Equal(6.0, response.GetType().GetProperty("result").GetValue(response));
        }

        [Fact]
        public void Calculate_Multiplication_ReturnsCorrectResult()
        {
            // Arrange
            double a = 7;
            double b = 6;
            string op = "multiply";

            // Act
            var result = _controller.Calculate(a, b, op) as OkObjectResult;

            // Assert
            Assert.NotNull(result);
            Assert.Equal(200, result.StatusCode);

            var response = result.Value;
            Assert.Equal(42.0, response.GetType().GetProperty("result").GetValue(response));
        }

        [Fact]
        public void Calculate_Division_ReturnsCorrectResult()
        {
            // Arrange
            double a = 20;
            double b = 4;
            string op = "divide";

            // Act
            var result = _controller.Calculate(a, b, op) as OkObjectResult;

            // Assert
            Assert.NotNull(result);
            Assert.Equal(200, result.StatusCode);

            var response = result.Value;
            Assert.Equal(5.0, response.GetType().GetProperty("result").GetValue(response));
        }

        [Fact]
        public void Calculate_DivisionByZero_ReturnsBadRequest()
        {
            // Arrange
            double a = 10;
            double b = 0;
            string op = "divide";

            // Act
            var result = _controller.Calculate(a, b, op) as BadRequestObjectResult;

            // Assert
            Assert.NotNull(result);
            Assert.Equal(400, result.StatusCode);

            var response = result.Value;
            Assert.Equal("Division by zero is not allowed.", response.GetType().GetProperty("error").GetValue(response));
        }

        [Fact]
        public void Calculate_InvalidOperator_ReturnsBadRequest()
        {
            // Arrange
            double a = 10;
            double b = 5;
            string op = "invalid";

            // Act
            var result = _controller.Calculate(a, b, op) as BadRequestObjectResult;

            // Assert
            Assert.NotNull(result);
            Assert.Equal(400, result.StatusCode);

            var response = result.Value;
            Assert.Equal("Invalid operator. Use add, subtract, multiply, or divide.", response.GetType().GetProperty("error").GetValue(response));
        }
    }
}