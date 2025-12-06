using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Scalar.AspNetCore;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using System.Text;


// Program.cs: ponto de entrada e configuração do servidor web.

var builder = WebApplication.CreateBuilder(args);


builder.Services.AddControllers()
    .AddNewtonsoftJson();

builder.Services.AddHttpClient();


var jwtSettings = builder.Configuration.GetSection("Jwt");
var secretKey = jwtSettings["Key"];


var pythonApiKey = builder.Configuration["PythonApiSettings:ApiKey"];

if (string.IsNullOrEmpty(secretKey) || secretKey.Length < 32)
{
    throw new InvalidOperationException("JWT Key não configurada ou muito curta.");
}

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

    options.Events = new JwtBearerEvents
    {
        OnMessageReceived = context =>
        {
            var accessToken = context.Request.Cookies["accessToken"];
            if (!string.IsNullOrEmpty(accessToken))
            {
                context.Token = accessToken;
            }
            return Task.CompletedTask;
        }
    };
});

builder.Services.AddAuthorization();

// Configurar CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.SetIsOriginAllowed(origin => 
                origin.StartsWith("http://localhost") || 
                origin.Contains("vercel.app") || 
                origin.Contains("netlify.app") ||
                origin.Contains("onrender.com") ||
                origin.Contains("azurecontainerapps.io") ||
                origin.Contains("azurestaticapps.net") ||
                origin.Contains("vps.gsilverio.com"))
              .AllowAnyMethod()
              .AllowAnyHeader()
              .AllowCredentials();
    });
});


builder.Services.AddOpenApi();

var app = builder.Build();


if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    
    
    app.MapScalarApiReference(options =>
    {
        options
            .WithTitle("Facial Analysis API")
            .WithTheme(ScalarTheme.Purple)
            .WithDefaultHttpClient(ScalarTarget.CSharp, ScalarClient.HttpClient);
    });
}

app.UseStaticFiles();
app.UseCors("AllowAll");

// Middleware simples para logar requisições em ambiente de desenvolvimento.
// Em produção, manter logs limpos e usar o sistema de logging configurado.
app.Use(async (context, next) =>
{
    if (app.Environment.IsDevelopment())
    {
        app.Logger.LogInformation("[Request] {method} {path}", context.Request.Method, context.Request.Path);
    }
    await next();
});


app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.MapGet("/health", async (IHttpClientFactory httpFactory, IConfiguration config) =>
{
    var pythonUrl = config["PythonApiSettings:BaseUrl"] ?? "http://localhost:5000";
    var apiKey = config["PythonApiSettings:ApiKey"] ?? string.Empty;

    try
    {
        var client = httpFactory.CreateClient();
        var url = pythonUrl.TrimEnd('/') + "/health";
        using var req = new HttpRequestMessage(HttpMethod.Get, url);
        if (!string.IsNullOrEmpty(apiKey)) req.Headers.Add("X-API-Key", apiKey);

        var resp = await client.SendAsync(req);
        if (resp.IsSuccessStatusCode)
            return Results.Ok(new { status = "healthy", python = true });

        return Results.Json(new { status = "degraded", python = false, code = (int)resp.StatusCode }, statusCode: 503);
    }
    catch (Exception ex)
    {
        return Results.Json(new { status = "unhealthy", error = ex.Message }, statusCode: 503);
    }
});

app.Run();

