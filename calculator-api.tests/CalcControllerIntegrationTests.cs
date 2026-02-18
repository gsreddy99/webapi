using System.Net;
using System.Net.Http.Json;
using Xunit;
using System.Text.Json;

public class CalcControllerIntegrationTests : IClassFixture<TestWebApplicationFactory>
{
    private readonly HttpClient _client;

    public CalcControllerIntegrationTests(TestWebApplicationFactory factory)
    {
        _client = factory.CreateClient();

        // Add fake API key to bypass middleware
        _client.DefaultRequestHeaders.Add("x-api-key", "test-key");
    }

    [Fact]
    public async Task Addition_Works()
    {
        var response = await _client.GetAsync("/api/calc?a=5&b=3&op=add");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var result = await response.Content.ReadFromJsonAsync<JsonElement>();
        Assert.Equal(8.0, result.GetProperty("result").GetDouble());
    }

    [Fact]
    public async Task Subtraction_Works()
    {
        var response = await _client.GetAsync("/api/calc?a=10&b=4&op=subtract");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var result = await response.Content.ReadFromJsonAsync<JsonElement>();
        Assert.Equal(6.0, result.GetProperty("result").GetDouble());
    }

    [Fact]
    public async Task Multiplication_Works()
    {
        var response = await _client.GetAsync("/api/calc?a=7&b=6&op=multiply");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var result = await response.Content.ReadFromJsonAsync<JsonElement>();
        Assert.Equal(42.0, result.GetProperty("result").GetDouble());
    }

    [Fact]
    public async Task Division_Works()
    {
        var response = await _client.GetAsync("/api/calc?a=20&b=4&op=divide");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var result = await response.Content.ReadFromJsonAsync<JsonElement>();
        Assert.Equal(5.0, result.GetProperty("result").GetDouble());
    }

    [Fact]
    public async Task DivideByZero_ReturnsBadRequest()
    {
        var response = await _client.GetAsync("/api/calc?a=10&b=0&op=divide");

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);

        var error = await response.Content.ReadAsStringAsync();
        Assert.Contains("Division by zero is not allowed", error);
    }

    [Fact]
    public async Task InvalidOperator_ReturnsBadRequest()
    {
        var response = await _client.GetAsync("/api/calc?a=5&b=5&op=invalid");

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);

        var error = await response.Content.ReadAsStringAsync();
        Assert.Contains("Invalid operator. Use add, subtract, multiply, or divide.", error);
    }
}