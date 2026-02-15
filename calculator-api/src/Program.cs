var builder = WebApplication.CreateBuilder(args);

// Controllers
builder.Services.AddControllers();

// Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Enable Application Insights
builder.Services.AddApplicationInsightsTelemetry();

builder.Services.AddSingleton(sp => { var kvUrl = builder.Configuration["KEYVAULT_URL"]; return new SecretClient(new Uri(kvUrl), new DefaultAzureCredential()); });

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.MapControllers();
app.Run();
