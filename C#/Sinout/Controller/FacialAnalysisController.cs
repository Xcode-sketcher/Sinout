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
        public async Task<IActionResult> AnalisarFace([FromForm] IFormFile file, [FromForm] string? model = "Facenet", [FromForm] string? detector = "opencv")
        {
            Console.WriteLine($"[DEBUG] 📥 Recebida requisição /analyze. File: {file?.FileName}, Size: {file?.Length}");
            try
            {
                var userId = GetCurrentUserId();
                var userRole = GetCurrentUserRole();
                var token = GetCurrentToken();

                if (file == null || file.Length == 0) return BadRequest(new { sucesso = false, message = "Nenhuma imagem enviada" });

                // Análise na API Python
                using var content = new MultipartFormDataContent();
                var imageBytes = await GetBytesFromFormFile(file);
                content.Add(new ByteArrayContent(imageBytes), "file", file.FileName);
                content.Add(new StringContent(model ?? "Facenet"), "model");
                content.Add(new StringContent(detector ?? "opencv"), "detector");
                content.Add(new StringContent("emotion,age,gender"), "actions");

                var pythonRequest = new HttpRequestMessage(HttpMethod.Post, $"{_pythonApiUrl}/analyze");
                pythonRequest.Content = content;
                pythonRequest.Headers.Add("X-API-Key", _pythonApiKey);

                Console.WriteLine($"[DEBUG] 🚀 Enviando para Python API: {_pythonApiUrl}/analyze");
                var response = await _httpClient.SendAsync(pythonRequest);
                
                if (!response.IsSuccessStatusCode)
                {
                    var errorBody = await response.Content.ReadAsStringAsync();
                    Console.WriteLine($"[DEBUG] ❌ Erro da Python API - Status: {response.StatusCode}");
                    Console.WriteLine($"[DEBUG] ❌ Corpo da resposta: {errorBody}");
                    return StatusCode((int)response.StatusCode, new { sucesso = false, message = "Erro na API Python", detalhes = errorBody });
                }

                var jsonResponse = await response.Content.ReadAsStringAsync();
                var resultado = JsonConvert.DeserializeObject<dynamic>(jsonResponse);

                var emocaoDominante = resultado?.analise?.emocao_dominante?.ToString() ?? "";
                var emocoes = resultado?.analise?.emocoes;
                var idade = resultado?.analise?.idade?.ToString();
                var genero = resultado?.analise?.genero?.ToString();

                return Ok(new 
                { 
                    sucesso = true, 
                    userId, 
                    userRole,
                    emocao = emocaoDominante, 
                    emocoes = emocoes,
                    idade = idade,
                    genero = genero
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[DEBUG] 💥 Exceção no Controller: {ex.Message}");
                Console.WriteLine(ex.StackTrace);
                return StatusCode(500, new { sucesso = false, message = "Ocorreu um erro interno no servidor.", detalhes = ex.Message, stackTrace = ex.StackTrace });
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

        [HttpGet("models")]
        public async Task<IActionResult> ListarModelos()
        {
            var req = new HttpRequestMessage(HttpMethod.Get, $"{_pythonApiUrl}/models");
            req.Headers.Add("X-API-Key", _pythonApiKey);
            var resp = await _httpClient.SendAsync(req);
            if (resp.IsSuccessStatusCode)
            {
                var content = await resp.Content.ReadAsStringAsync();
                return Ok(JsonConvert.DeserializeObject<dynamic>(content));
            }
            return StatusCode((int)resp.StatusCode, new { sucesso = false, erro = "Erro ao buscar modelos" });
        }

        [HttpPost("analyze-base64")]
        public async Task<IActionResult> AnalisarFaceBase64([FromBody] AnalyzeRequest request)
        {
            try
            {
                var userId = GetCurrentUserId();
                var userRole = GetCurrentUserRole();
                var token = GetCurrentToken();

                if (string.IsNullOrEmpty(request.ImageBase64)) return BadRequest(new { sucesso = false, erro = "Nenhuma imagem enviada" });

                var payload = new
                {
                    image_base64 = request.ImageBase64,
                    model = request.Model ?? "Facenet",
                    detector = request.Detector ?? "opencv",
                    actions = new[] { "emotion", "age", "gender" }
                };

                var pythonRequest = new HttpRequestMessage(HttpMethod.Post, $"{_pythonApiUrl}/analyze-base64");
                pythonRequest.Content = new StringContent(JsonConvert.SerializeObject(payload), Encoding.UTF8, "application/json");
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

                
                var emailClaim = User.FindFirst(ClaimTypes.Email)?.Value ?? User.FindFirst("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress")?.Value;
                string patientName = emailClaim ?? "Paciente"; // Use email do JWT como identificador

                
                var emotionData = new
                {
                    CuidadorId = userId,
                    PatientName = patientName,
                    EmotionsDetected = emocoes,
                    DominantEmotion = emocaoDominante,
                    Age = idade,
                    Gender = genero,
                    Timestamp = DateTime.UtcNow
                };

                var crudRequest = new HttpRequestMessage(HttpMethod.Post, $"{_crudApiUrl}/api/history/cuidador-emotion");
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
                return StatusCode(500, new { sucesso = false, erro = "Ocorreu um erro interno no servidor.", detalhes = ex.Message, stackTrace = ex.StackTrace });
            }
        }

        private string GetCurrentUserId()
        {
            
            var allClaims = User.Claims.Select(c => $"{c.Type}: {c.Value}").ToList();
           
            
            var userIdClaim = User.FindFirst("userId");
            if (userIdClaim == null)
            {
                
                userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier) ?? User.FindFirst("nameid") ?? User.FindFirst("sub");
                if (userIdClaim == null)
                    throw new UnauthorizedAccessException("Token JWT inválido");
            }
            
            if (string.IsNullOrWhiteSpace(userIdClaim.Value))
                throw new UnauthorizedAccessException("Token JWT inválido");
            
            return userIdClaim.Value;
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
