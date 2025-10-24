using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using Newtonsoft.Json;
using Sinout.Model;

namespace Sinout.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class FacialAnalysisController : ControllerBase
    {
        private readonly HttpClient _httpClient;
        private const string PYTHON_API_URL = "http://localhost:5000"; // API Flask interna

        public FacialAnalysisController(IHttpClientFactory httpClientFactory)
        {
            _httpClient = httpClientFactory.CreateClient();
            _httpClient.Timeout = TimeSpan.FromSeconds(30);
        }

        /// <summary>
        /// Endpoint público - Usuário envia imagem aqui
        /// </summary>
        /// <param name="file">Arquivo de imagem (JPEG, PNG, etc.)</param>
        /// <param name="model">Modelo de reconhecimento facial. Opções: VGG-Face, Facenet, Facenet512, OpenFace, DeepFace, DeepID, ArcFace, Dlib, SFace. Default: Facenet</param>
        /// <returns>Análise facial com emoção, idade e gênero</returns>
        [HttpPost("analyze")]
        public async Task<IActionResult> AnalisarFace([FromForm] IFormFile file, [FromForm] string? model = "Facenet")

        {
            try
            {
                if (file == null || file.Length == 0)
                {
                    return BadRequest(new { sucesso = false, erro = "Nenhuma imagem enviada" });
                }

                // Preparar requisição para API Python
                using var content = new MultipartFormDataContent();

                // Adicionar arquivo
                var imageBytes = await GetBytesFromFormFile(file);
                content.Add(new ByteArrayContent(imageBytes), "file", file.FileName);

                // Adicionar modelo (opcional)
                content.Add(new StringContent(model ?? "Facenet"), "model");

                // Adicionar ações
                content.Add(new StringContent("emotion,age,gender"), "actions");

                // Enviar para API Python Flask
                var response = await _httpClient.PostAsync($"{PYTHON_API_URL}/analyze", content);

                if (!response.IsSuccessStatusCode)
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    return StatusCode((int)response.StatusCode, new 
                    { 
                        sucesso = false, 
                        erro = "Erro na API Python",
                        detalhes = errorContent 
                    });
                }

                // Ler resposta JSON do Python
                var jsonResponse = await response.Content.ReadAsStringAsync();
                var resultado = JsonConvert.DeserializeObject<dynamic>(jsonResponse);

                // Aqui você pode processar/reformatar os dados antes de retornar
                // Por exemplo, salvar no banco de dados, adicionar informações extras, etc.

                return Ok(resultado);
            }
            catch (Exception ex)
            {
                return StatusCode(500, new 
                { 
                    sucesso = false, 
                    erro = "Erro no servidor C#", 
                    mensagem = ex.Message 
                });
            }
        }

        /// <summary>
        /// Analisa usando base64 (alternativa)
        /// </summary>
        /// <param name="request">Objeto com ImageBase64 e Model (opcional)</param>
        /// <returns>Análise facial com emoção, idade e gênero</returns>
        [HttpPost("analyze-base64")]
        public async Task<IActionResult> AnalisarFaceBase64([FromBody] AnalyzeRequest request)
        {
            try
            {
                if (string.IsNullOrEmpty(request.ImageBase64))
                {
                    return BadRequest(new { sucesso = false, erro = "image_base64 é obrigatório" });
                }

                // Preparar JSON para enviar ao Python
                var jsonContent = JsonConvert.SerializeObject(new
                {
                    image_base64 = request.ImageBase64,
                    model = request.Model ?? "Facenet",
                    actions = new[] { "emotion", "age", "gender" }
                });

                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                // Enviar para API Python
                var response = await _httpClient.PostAsync($"{PYTHON_API_URL}/analyze-base64", content);

                if (!response.IsSuccessStatusCode)
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    return StatusCode((int)response.StatusCode, new { sucesso = false, erro = errorContent });
                }

                var jsonResponse = await response.Content.ReadAsStringAsync();
                var resultado = JsonConvert.DeserializeObject<dynamic>(jsonResponse);

                return Ok(resultado);
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { sucesso = false, erro = ex.Message });
            }
        }

        /// <summary>
        /// Verifica se API Python está online
        /// </summary>
        [HttpGet("health")]
        public async Task<IActionResult> VerificarSaude()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{PYTHON_API_URL}/health");

                if (response.IsSuccessStatusCode)
                {
                    var jsonResponse = await response.Content.ReadAsStringAsync();
                    return Ok(new 
                    { 
                        sucesso = true, 
                        mensagem = "API Python está online",
                        detalhes = JsonConvert.DeserializeObject<dynamic>(jsonResponse)
                    });
                }

                return StatusCode(503, new { sucesso = false, erro = "API Python não está respondendo" });
            }
            catch (Exception ex)
            {
                return StatusCode(503, new 
                { 
                    sucesso = false, 
                    erro = "Não foi possível conectar à API Python", 
                    mensagem = ex.Message 
                });
            }
        }

        /// <summary>
        /// Lista modelos disponíveis
        /// </summary>
        [HttpGet("models")]
        public async Task<IActionResult> ListarModelos()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{PYTHON_API_URL}/models");
                var jsonResponse = await response.Content.ReadAsStringAsync();
                var resultado = JsonConvert.DeserializeObject<dynamic>(jsonResponse);

                return Ok(resultado);
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { sucesso = false, erro = ex.Message });
            }
        }

        // Método auxiliar
        private async Task<byte[]> GetBytesFromFormFile(IFormFile file)
        {
            using var memoryStream = new MemoryStream();
            await file.CopyToAsync(memoryStream);
            return memoryStream.ToArray();
        }
    }

}
