using Azure.Identity;
using Azure.Security.KeyVault.Secrets;
using System.Text.Json.Serialization;

var builder = WebApplication.CreateBuilder(args);

// Controllers + JSON fix
builder.Services.AddControllers().AddJsonOptions(options =>
{
    options.JsonSerializerOptions.NumberHandling =
        JsonNumberHandling.AllowNamedFloatingPointLiterals;
});

// Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Application Insights
builder.Services.AddApplicationInsightsTelemetry();

// Key Vault client
builder.Services.AddSingleton(sp =>
{
    var kvUrl = builder.Configuration["KEYVAULT_URL"];
    return new SecretClient(new Uri(kvUrl), new DefaultAzureCredential());
});

// Read API key from Key Vault at startup
var kvUrl2 = builder.Configuration["KEYVAULT_URL"];
var secretClient = new SecretClient(new Uri(kvUrl2), new DefaultAzureCredential());
var expectedApiKey = (await secretClient.GetSecretAsync("WebAppApiKey")).Value.Value;
builder.Configuration["EXPECTED_API_KEY"] = expectedApiKey;

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// Middleware to validate x-api-key
app.Use(async (context, next) =>
{
    var expectedKey = context.RequestServices
        .GetRequiredService<IConfiguration>()["EXPECTED_API_KEY"];

    if (!context.Request.Headers.TryGetValue("x-api-key", out var providedKey) ||
        providedKey != expectedKey)
    {
        context.Response.StatusCode = 401;
        await context.Response.WriteAsync("Unauthorized");
        return;
    }

    await next();
});

app.UseHttpsRedirection();
app.MapControllers();
app.Run();
