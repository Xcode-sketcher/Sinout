using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);

// Adicionar serviços
builder.Services.AddControllers()
    .AddNewtonsoftJson(); // Para suporte a JSON

// Configurar HttpClient para fazer chamadas à API Python
builder.Services.AddHttpClient();

// Configurar CORS (se necessário para front-end)
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// OpenAPI para documentação
builder.Services.AddOpenApi();

var app = builder.Build();

// Configurar pipeline HTTP
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    
    // Adicionar Scalar API Documentation(Documentação automatica de API)
    app.MapScalarApiReference(options =>
    {
        options
            .WithTitle("Facial Analysis API")
            .WithTheme(ScalarTheme.Purple)
            .WithDefaultHttpClient(ScalarTarget.CSharp, ScalarClient.HttpClient);
    });
}

// Servir arquivos estáticos (HTML de exemplo)
app.UseStaticFiles();
app.UseCors("AllowAll");
app.UseAuthorization();
app.MapControllers();

//Seção visual do console
Console.WriteLine("=============================================================");
Console.WriteLine("🚀 API ASP.NET rodando!");
Console.WriteLine("📍 URL: https://localhost:5001 (ou http://localhost:5000)");
Console.WriteLine("📘 Scalar API Docs: https://localhost:5001/scalar/v1");
Console.WriteLine("🔗 OpenAPI JSON: https://localhost:5001/openapi/v1.json");
Console.WriteLine("=============================================================");
Console.WriteLine("⚠️  Certifique-se de que a API Python Flask está rodando!");
Console.WriteLine("   python api_deepface_flask.py ou a versão debug");
Console.WriteLine("=============================================================");

app.Run();
