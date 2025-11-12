using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Scalar.AspNetCore;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

// Adicionar serviços
builder.Services.AddControllers()
    .AddNewtonsoftJson(); // Para suporte a JSON

// Configurar HttpClient para fazer chamadas à API Python
builder.Services.AddHttpClient();

// ===== CONFIGURAÇÃO JWT AUTHENTICATION =====
var jwtSettings = builder.Configuration.GetSection("Jwt");
var secretKey = jwtSettings["Key"];

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey)),
        ValidateIssuer = true,
        ValidIssuer = jwtSettings["Issuer"],
        ValidateAudience = true,
        ValidAudience = jwtSettings["Audience"],
        ValidateLifetime = true,
        ClockSkew = TimeSpan.Zero
    };
});

builder.Services.AddAuthorization();

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

// ===== ATIVAR AUTENTICAÇÃO E AUTORIZAÇÃO =====
app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

//Seção visual do console
Console.WriteLine("=============================================================");
Console.WriteLine("🚀 API ASP.NET rodando!");
Console.WriteLine("📍 URL: https://localhost:7125 (ou http://localhost:5236)");
Console.WriteLine("📘 Scalar API Docs: https://localhost:7125/scalar/v1");
Console.WriteLine("🔗 OpenAPI JSON: https://localhost:7125/openapi/v1.json");
Console.WriteLine("🔐 JWT Authentication: ATIVADO");
Console.WriteLine("🔑 Python API Key: CONFIGURADO");
Console.WriteLine("=============================================================");
Console.WriteLine("⚠️  Certifique-se de que a API Python Flask está rodando!");
Console.WriteLine("   python api_deepface_flask.py ou a versão debug");
Console.WriteLine("=============================================================");

app.Run();

