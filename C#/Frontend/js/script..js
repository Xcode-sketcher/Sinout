let stream = null;
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

// Inicializar câmera
async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
            },
        });

        video.srcObject = stream;

        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        };

        document.getElementById("startBtn").disabled = true;
        document.getElementById("captureBtn").disabled = false;
        document.getElementById("stopBtn").disabled = false;

        showStatus("Câmera ativada!", "connected");
    } catch (error) {
        showError("Erro ao acessar câmera: " + error.message);
    }
}

// Parar câmera
function stopCamera() {
    if (stream) {
        stream.getTracks().forEach((track) => track.stop());
        video.srcObject = null;
        stream = null;
    }

    document.getElementById("startBtn").disabled = false;
    document.getElementById("captureBtn").disabled = true;
    document.getElementById("stopBtn").disabled = true;

    showStatus("Câmera desativada", "disconnected");
}

// Capturar frame e enviar para análise
async function captureAndAnalyze() {
    // Desenhar frame atual no canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Converter canvas para blob
    canvas.toBlob(
        async (blob) => {
            if (!blob) {
                showError("Erro ao capturar imagem");
                return;
            }

            // Enviar para API
            await sendImageToAPI(blob);
        },
        "image/jpeg",
        0.95
    );
}

// Enviar imagem para API Flask(Python)
async function sendImageToAPI(imageBlob) {
    const apiUrl = document.getElementById("apiUrl").value;
    const model = document.getElementById("modelSelect").value;

    showLoading(true);
    hideError();
    hideResults();

    try {
        const formData = new FormData();
        formData.append("file", imageBlob, "capture.jpg");
        formData.append("model", model);
        formData.append("actions", "emotion,age,gender");


        const endpoint = apiUrl.includes(':5236')
            ? '/api/FacialAnalysis/analyze'
            : '/analyze';

        const response = await fetch(`${apiUrl}${endpoint}`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (data.sucesso) {
            displayResults(data);
        } else {
            showError("Erro na análise: " + data.erro);
        }
    } catch (error) {
        showError("Erro ao conectar com API: " + error.message);
    } finally {
        showLoading(false);
    }
}

// Exibir resultados do reconhecimento facial
function displayResults(data) {
    const analise = data.analise;

    // Emoção dominante
    document.getElementById("dominantEmotion").textContent =
        translateEmotion(analise.emocao_dominante);

    // Idade e gênero (Remover no futuro, afinal o usuário não quer a estimativa de sua idade sendo exibida sempre)
    document.getElementById("age").textContent =
        Math.round(analise.idade) + " anos";
    document.getElementById("gender").textContent =
        analise.genero === "Man" ? "Masculino" : "Feminino";
    document.getElementById("model").textContent = data.modelo_usado;

    // Grid de emoções
    const emotionsGrid = document.getElementById("emotionsGrid");
    emotionsGrid.innerHTML = "";

    const emotions = analise.emocoes;
    const sortedEmotions = Object.entries(emotions).sort(
        (a, b) => b[1] - a[1]
    );

    //Laço de repetição para criação das barras de emoções com valores dinâmicos
    sortedEmotions.forEach(([emotion, value]) => {
        const card = document.createElement("div");
        card.className = "emotion-card";
        card.innerHTML = `
                    <div class="emotion-name">${translateEmotion(emotion)}</div>
                    <div class="emotion-bar">
                        <div class="emotion-fill" style="width: ${value}%"></div>
                    </div>
                    <div class="emotion-value">${value.toFixed(2)}%</div>
                `;
        emotionsGrid.appendChild(card);
    });

    document.getElementById("results").classList.add("show");
}

// Recebe as emoções capturadas(JSON) e transforma em palavas a serem exibidas
function translateEmotion(emotion) {
    const translations = {
        happy: "Feliz 😊",
        sad: "Triste 😢",
        angry: "Bravo 😠",
        surprise: "Surpreso 😲",
        fear: "Medo 😨",
        disgust: "Nojo 🤢",
        neutral: "Neutro 😐",
    };
    return translations[emotion] || emotion;
}

// Verificar disponibilidade de API (Terá utilidade após o deploy)
async function checkAPIHealth() {
    const apiUrl = document.getElementById("apiUrl").value;

    try {
        const response = await fetch(`${apiUrl}/health`);
        const data = await response.json();

        if (data.status === "healthy") {
            showStatus("✅ API Flask está online e funcionando!", "connected");
        } else {
            showStatus(
                "⚠️ API respondeu mas pode ter problemas",
                "disconnected"
            );
        }
    } catch (error) {
        showStatus(
            "❌ Não foi possível conectar à API Flask",
            "disconnected"
        );
        showError(
            "Certifique-se de que a API está rodando: python api_deepface_flask.py"
        );
    }
}

// Funções adicionais para exibir, remover, ou adicionar erros/mensagens
function showLoading(show) {
    document.getElementById("loading").classList.toggle("show", show);
}

function showError(message) {
    const errorDiv = document.getElementById("error");
    errorDiv.textContent = message;
    errorDiv.classList.add("show");
}

function hideError() {
    document.getElementById("error").classList.remove("show");
}

function hideResults() {
    document.getElementById("results").classList.remove("show");
}

function showStatus(message, type) {
    const statusDiv = document.getElementById("status");
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
}

// Verificar API ao carregar página
window.addEventListener("load", () => {
    checkAPIHealth();
});