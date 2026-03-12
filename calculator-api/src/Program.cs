using System.Text.Json.Serialization;
using Azure.Identity;
using Azure.Security.KeyVault.Secrets;

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

// Key Vault + API key loading
if (!builder.Environment.IsDevelopment())
{
    // Register SecretClient in DI
    builder.Services.AddSingleton(sp =>
    {
        var kvUrl = builder.Configuration["KEYVAULT_URL"];
        return new SecretClient(new Uri(kvUrl), new DefaultAzureCredential());
    });

    // Load API key at startup
    var kvUrl2 = builder.Configuration["KEYVAULT_URL"];
    var secretClient = new SecretClient(new Uri(kvUrl2), new DefaultAzureCredential());
    var expectedApiKey = (await secretClient.GetSecretAsync("WebAppApiKey")).Value.Value;

    builder.Configuration["EXPECTED_API_KEY"] = expectedApiKey;
}
else
{
    // Local development fallback
    builder.Configuration["EXPECTED_API_KEY"] = "local-dev-key";
}

var app = builder.Build();

// Swagger UI
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// REQUIRED: Routing middleware
app.UseRouting();

// API key middleware (disabled locally)
if (!app.Environment.IsDevelopment())
{
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
}

// Authorization (safe default)
app.UseAuthorization();

// REQUIRED: Map controllers AFTER routing
app.MapControllers();

app.Run();

// Required for integration testing
public partial class Program { }
