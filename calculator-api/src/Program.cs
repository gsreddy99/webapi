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

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.MapControllers();
app.Run();
