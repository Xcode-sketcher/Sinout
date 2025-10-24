# 🚀 Sinout

## 📋 Visão Geral do Projeto

Sistema completo de análise facial que integra uma API Python (DeepFace) com uma API C# ASP.NET, permitindo detecção de emoções, idade e gênero a partir de imagens.

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐      ┌──────────┐
│   Frontend  │ ───> │  API C#      │ ───> │  API Python     │ ───> │ DeepFace │
│   (HTML/JS) │      │  ASP.NET     │      │  Flask          │      │          │
└─────────────┘      └──────────────┘      └─────────────────┘      └──────────┘
```

**Fluxo de Dados:**
- Frontend captura imagem via câmera ou upload
- API C# (pública) recebe requisição do usuário
- API Python (interna) processa com DeepFace
- Resposta JSON retorna através do C# para o frontend

---

## 📁 Estrutura do Projeto

```
projeto/
├── C#/                                    # Backend ASP.NET
│   ├── C#.sln                            # Solution do projeto
│   ├── Frontend/                          # Interface web
│   │   ├── frontend_camera.html          # Página principal
│   │   ├── js/
│   │   │   └── script..js                # Lógica frontend
│   │   └── style/
│   │       └── style.css                 # Estilos
│   └── Sinout/                           # Projeto API C#
│       ├── Program.cs                    # Configuração da API
│       ├── Sinout.csproj                 # Configurações do projeto
│       ├── Controller/
│       │   └── FacialAnalysisController.cs  # Controller principal
│       ├── Model/
│       │   └── AnalyzeRequest.cs         # Modelos de dados
│       ├── Properties/
│       │   └── launchSettings.json       # Configurações de execução
│       └── wwwroot/                      # Arquivos estáticos
│
└── PythonDeepFaceApi/                     # Backend Python
    ├── api_deepface_flask.py             # API Flask (produção)
    ├── api_deepface_flask_debug.py       # API Flask (debug)
    ├── requirements.txt                  # Dependências Python
    └── README.md                         # Documentação detalhada
```

---

## 🛠️ Tecnologias Utilizadas

### Backend C# (.NET)
- **ASP.NET Core** - Framework web
- **Newtonsoft.Json** - Manipulação JSON
- **HttpClient** - Comunicação com API Python

### Backend Python
- **Flask** - Framework web
- **DeepFace** - Biblioteca de análise facial
- **OpenCV** - Processamento de imagens
- **TensorFlow** - Machine Learning

### Frontend
- **HTML5** - Estrutura
- **CSS3** - Estilização
- **JavaScript** - Interatividade
- **MediaDevices API** - Acesso à câmera

---

## ⚙️ Pré-requisitos

- **Python 3.9+**
- **.NET 6.0+**
- **Navegador moderno** (Chrome, Firefox, Edge)
- **Câmera** (para captura de imagens)

---

## 🚀 Como Executar o Projeto

### 1. Configurar API Python

```bash
# Navegar para a pasta Python
cd PythonDeepFaceApi

# Instalar dependências
pip install flask flask-cors deepface opencv-python tensorflow

# Executar a API
python api_deepface_flask.py
```

**Resultado esperado:**
```
🚀 API DeepFace Flask - Modo Interno
✅ Servidor iniciando...
📍 URL: http://localhost:5000
```

---

### 2. Configurar API C#

```bash
# Navegar para a pasta do projeto C#
cd C#/Sinout

# Restaurar dependências
dotnet restore

# Executar a API
dotnet run
```

**Resultado esperado:**
```
🚀 API ASP.NET rodando!
📍 URL: https://localhost:5001
📚 Swagger: https://localhost:5001/swagger
```

---

### 3. Abrir Frontend

Abra o arquivo no navegador:
```
C#/Frontend/frontend_camera.html
```

Ou configure um servidor local.

---

## 🎯 Endpoints da API C# (Pública)

### 1. Analisar Imagem
```http
POST /api/FacialAnalysis/analyze
Content-Type: multipart/form-data

Body:
  - image: arquivo de imagem
  - model: "Facenet" (opcional)
```

### 2. Analisar Base64
```http
POST /api/FacialAnalysis/analyze-base64
Content-Type: application/json

Body:
{
  "imageBase64": "base64_string_aqui",
  "model": "Facenet"
}
```

### 3. Health Check
```http
GET /api/FacialAnalysis/health
```

### 4. Listar Modelos
```http
GET /api/FacialAnalysis/models
```

---

## 📊 Endpoints da API Python (Interna)

### 1. Informações da API
```http
GET /
```

### 2. Health Check
```http
GET /health
```

### 3. Listar Modelos
```http
GET /models
```

### 4. Analisar Imagem (Multipart)
```http
POST /analyze
Content-Type: multipart/form-data
```

### 5. Analisar Base64
```http
POST /analyze-base64
Content-Type: application/json
```

### 6. Múltiplas Faces
```http
POST /analyze-multiple
Content-Type: multipart/form-data
```

---

## 🔄 Fluxo de Comunicação

1. **Usuário** interage com o frontend (HTML/JS)
2. **Frontend** envia imagem para API C# (HTTPS)
3. **API C#** valida e repassa para API Python (HTTP interno)
4. **API Python** processa com DeepFace
5. **API Python** retorna análise em JSON
6. **API C#** formata e retorna ao frontend
7. **Frontend** exibe resultados ao usuário

**Importante:** A API Python NÃO é acessada diretamente pelo usuário.

---

## 📝 Exemplo de Resposta

```json
{
  "sucesso": true,
  "timestamp": "2025-10-24T15:30:00",
  "modelo_usado": "Facenet",
  "analise": {
    "emocao_dominante": "happy",
    "emocoes": {
      "happy": 95.3,
      "neutral": 2.1,
      "surprise": 1.5,
      "sad": 0.8,
      "angry": 0.2,
      "fear": 0.1,
      "disgust": 0.0
    },
    "idade": 28,
    "genero": "Man",
    "confianca_genero": 98.5
  }
}
```

---

## 🐛 Solução de Problemas

### ❌ "Não foi possível conectar à API Python"
- Verifique se a API Python está rodando: `python api_deepface_flask.py`
- Confirme a porta: `http://localhost:5000`

### ❌ "CORS error" no frontend
- Já configurado no `Program.cs`
- Verifique se `app.UseCors("AllowAll")` está presente

### ❌ Python demora muito para responder
- Primeira requisição é mais lenta (carrega modelo)
- Use modelos mais rápidos: `Facenet` ou `OpenFace`

### ❌ "ModuleNotFoundError: No module named 'deepface'"
```bash
pip install deepface opencv-python tensorflow
```

### ❌ Câmera não funciona no frontend
- Use HTTPS ou localhost
- Verifique permissões do navegador

---

## ✅ Checklist de Verificação

- [ ] Python 3.9+ instalado
- [ ] .NET 6+ instalado
- [ ] Dependências Python instaladas
- [ ] API Python rodando (http://localhost:5000)
- [ ] API C# rodando (https://localhost:5001)
- [ ] Health check retorna sucesso
- [ ] Frontend abre corretamente
- [ ] Câmera funciona no navegador

---

## 🔒 Segurança

- API Python roda apenas internamente (localhost)
- API C# é a única interface pública
- Validações de entrada em ambas APIs
- CORS configurado adequadamente
- HTTPS habilitado no C#

---

## 🚀 Próximos Passos

### Desenvolvimento:
- [ ] Adicionar autenticação JWT
- [ ] Implementar banco de dados
- [ ] Criar biblioteca de classes (DDD/Clean Architecture)
- [ ] Adicionar testes unitários
- [ ] Melhorar tratamento de erros

### Produção:
- [ ] Configurar API Python como serviço
- [ ] Implementar rate limiting
- [ ] Adicionar logs estruturados
- [ ] Configurar CI/CD

---

## 📚 Documentação Adicional

Para mais detalhes sobre a integração Python + C#, consulte:
- `PythonDeepFaceApi/README.md` - Guia detalhado de integração

---

## 📄 Licença

Projeto temporariamente sem licença.

---

## 👨‍💻 Autor

Sinout - 2025
