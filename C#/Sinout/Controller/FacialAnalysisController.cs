using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using Newtonsoft.Json;
using Sinout.Model;
using System.Security.Claims;

namespace Sinout.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]
    public class FacialAnalysisController : ControllerBase
    {
        private readonly HttpClient _httpClient;
        private readonly IConfiguration _configuration;
        private readonly string _pythonApiUrl;
        private readonly string _pythonApiKey;
        private readonly string _crudApiUrl;

        public FacialAnalysisController(IHttpClientFactory httpClientFactory, IConfiguration configuration)
        {
            _httpClient = httpClientFactory.CreateClient();
            _httpClient.Timeout = TimeSpan.FromSeconds(30);
            _configuration = configuration;
            
            _pythonApiUrl = _configuration["PythonApiSettings:BaseUrl"] ?? "http://localhost:5000";
            _pythonApiKey = _configuration["PythonApiSettings:ApiKey"] ?? "";
            _crudApiUrl = _configuration["CrudApiSettings:BaseUrl"] ?? "http://localhost:5240";
        }

        [HttpPost("analyze")]
        public async Task<IActionResult> AnalisarFace([FromForm] IFormFile file, [FromForm] string? model = "Facenet")
        {
            try
            {
                var userId = GetCurrentUserId();
                var userRole = GetCurrentUserRole();
                var token = GetCurrentToken();

                if (file == null || file.Length == 0) return BadRequest(new { sucesso = false, erro = "Nenhuma imagem enviada" });

                // Análise na API Python
                using var content = new MultipartFormDataContent();
                var imageBytes = await GetBytesFromFormFile(file);
                content.Add(new ByteArrayContent(imageBytes), "file", file.FileName);
                content.Add(new StringContent(model ?? "Facenet"), "model");
                content.Add(new StringContent("emotion,age,gender"), "actions");

                var pythonRequest = new HttpRequestMessage(HttpMethod.Post, $"{_pythonApiUrl}/analyze");
                pythonRequest.Content = content;
                pythonRequest.Headers.Add("X-API-Key", _pythonApiKey);

                var response = await _httpClient.SendAsync(pythonRequest);
                if (!response.IsSuccessStatusCode) 
                    return StatusCode((int)response.StatusCode, new { sucesso = false, erro = "Erro na API Python" });

                var jsonResponse = await response.Content.ReadAsStringAsync();
                var resultado = JsonConvert.DeserializeObject<dynamic>(jsonResponse);

                var emocaoDominante = resultado?.analise?.emocao_dominante?.ToString() ?? "";
                var emocoes = resultado?.analise?.emocoes;
                var idade = resultado?.analise?.idade?.ToString();
                var genero = resultado?.analise?.genero?.ToString();

                // Buscar nome do paciente do perfil do usuário
                string patientName = "Paciente"; // Default fallback
                try
                {
                    var userProfileRequest = new HttpRequestMessage(HttpMethod.Get, $"{_crudApiUrl}/api/users/me");
                    userProfileRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                    
                    var userProfileResponse = await _httpClient.SendAsync(userProfileRequest);
                    if (userProfileResponse.IsSuccessStatusCode)
                    {
                        var userJson = await userProfileResponse.Content.ReadAsStringAsync();
                        var userProfile = JsonConvert.DeserializeObject<dynamic>(userJson);
                        patientName = userProfile?.patientName?.ToString() ?? "Paciente";
                        Console.WriteLine($"[DEBUG] Nome do paciente carregado do perfil: '{patientName}'");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[DEBUG] Erro ao buscar nome do paciente: {ex.Message}");
                }

                // Salvar histórico vinculado ao cuidador (sem PatientId)
                var emotionData = new 
                { 
                    CaregiverId = userId,
                    PatientName = patientName,
                    EmotionsDetected = emocoes, 
                    DominantEmotion = emocaoDominante,
                    Timestamp = DateTime.UtcNow
                };

                Console.WriteLine($"[DEBUG] Enviando para CRUD API: {JsonConvert.SerializeObject(emotionData)}");

                var crudRequest = new HttpRequestMessage(HttpMethod.Post, $"{_crudApiUrl}/api/history/caregiver-emotion");
                crudRequest.Content = new StringContent(JsonConvert.SerializeObject(emotionData), Encoding.UTF8, "application/json");
                crudRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

                var crudResponse = await _httpClient.SendAsync(crudRequest);
                string? mensagem = null;
                bool salvoNoHistorico = false;

                if (crudResponse.IsSuccessStatusCode)
                {
                    var crudJson = await crudResponse.Content.ReadAsStringAsync();
                    var crudResult = JsonConvert.DeserializeObject<dynamic>(crudJson);
                    mensagem = crudResult?.suggestedMessage?.ToString();
                    salvoNoHistorico = true;
                    Console.WriteLine($"[DEBUG] ✅ Histórico salvo com sucesso! Mensagem: {mensagem ?? "NENHUMA"}");
                }
                else
                {
                    var errorContent = await crudResponse.Content.ReadAsStringAsync();
                    Console.WriteLine($"[DEBUG] ❌ Erro ao salvar histórico: Status={crudResponse.StatusCode}, Body={errorContent}");
                }

                return Ok(new 
                { 
                    sucesso = true, 
                    userId, 
                    userRole,
                    emocao = emocaoDominante, 
                    emocoes = emocoes,
                    idade = idade,
                    genero = genero,
                    mensagem_sugerida = mensagem,
                    salvo_no_historico = salvoNoHistorico
                });
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { sucesso = false, erro = ex.Message, stack = ex.StackTrace });
            }
        }

        [HttpGet("health")]
        public async Task<IActionResult> VerificarSaude()
        {
            var req = new HttpRequestMessage(HttpMethod.Get, $"{_pythonApiUrl}/health");
            req.Headers.Add("X-API-Key", _pythonApiKey);
            var resp = await _httpClient.SendAsync(req);
            return resp.IsSuccessStatusCode ? Ok(new { sucesso = true }) : StatusCode(503, new { sucesso = false });
        }

        private int GetCurrentUserId()
        {
            // Debug: log all claims
            var allClaims = User.Claims.Select(c => $"{c.Type}: {c.Value}").ToList();
            Console.WriteLine("Available claims: " + string.Join(", ", allClaims));
            
            var userIdClaim = User.FindFirst("userId");
            if (userIdClaim == null)
            {
                // Fallback para outros claims
                userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier) ?? User.FindFirst("nameid") ?? User.FindFirst("sub");
                if (userIdClaim == null)
                    throw new UnauthorizedAccessException("Token JWT inválido - nenhum claim de ID encontrado. Claims disponíveis: " + string.Join(", ", allClaims));
            }
            
            if (string.IsNullOrWhiteSpace(userIdClaim.Value))
                throw new UnauthorizedAccessException("Token JWT inválido - claim de ID está vazio");
            
            if (!int.TryParse(userIdClaim.Value, out int userId))
                throw new UnauthorizedAccessException($"Token JWT inválido - claim '{userIdClaim.Type}' com valor '{userIdClaim.Value}' não é um número válido");
            
            return userId;
        }
        
        private string? GetCurrentUserRole() => User.FindFirst(ClaimTypes.Role)?.Value;
        private string GetCurrentToken() => Request.Headers["Authorization"].ToString().Replace("Bearer ", "").Trim();

        private async Task<byte[]> GetBytesFromFormFile(IFormFile file)
        {
            using var ms = new MemoryStream();
            await file.CopyToAsync(ms);
            return ms.ToArray();
        }
    }
}
