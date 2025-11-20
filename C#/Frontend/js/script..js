let stream = null;
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");


async function startCamera() {
    console.log("[DEBUG] Iniciando câmera...");

    try {
        const constraints = {
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
            },
        };

        console.log("[DEBUG] Solicitando acesso à câmera com constraints:", constraints);

        stream = await navigator.mediaDevices.getUserMedia(constraints);
        console.log("[DEBUG] Stream obtido com sucesso");

        video.srcObject = stream;

        video.onloadedmetadata = () => {
            console.log("[DEBUG] Video metadata loaded:", video.videoWidth, "x", video.videoHeight);
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            console.log("[DEBUG] Canvas configurado:", canvas.width, "x", canvas.height);
        };

        document.getElementById("startBtn").disabled = true;
        document.getElementById("captureBtn").disabled = false;
        document.getElementById("stopBtn").disabled = false;

        showStatus("Câmera ativada!", "connected");
    } catch (error) {
        console.error("[DEBUG] Erro ao acessar câmera:", error);
        showError("Erro ao acessar câmera: " + error.message);
    }
}


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


async function captureAndAnalyze() {
    console.log("[DEBUG] Iniciando captura e análise...");


    if (canvas.width === 0 || canvas.height === 0) {
        console.error("[DEBUG] Canvas não tem dimensões válidas:", canvas.width, canvas.height);
        showError("Erro: câmera não foi inicializada corretamente");
        return;
    }


    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    console.log("[DEBUG] Frame desenhado no canvas:", canvas.width, "x", canvas.height);


    canvas.toBlob(
        async (blob) => {
            if (!blob) {
                console.error("[DEBUG] Falha ao converter canvas para blob");
                showError("Erro ao capturar imagem");
                return;
            }

            console.log("[DEBUG] Blob criado com tamanho:", blob.size, "bytes");
            console.log("[DEBUG] Tipo do blob:", blob.type);


            await sendImageToAPI(blob);
        },
        "image/jpeg",
        0.95
    );
}


async function sendImageToAPI(imageBlob) {
    const apiUrl = document.getElementById("apiUrl").value;
    const model = document.getElementById("modelSelect").value;

    console.log("[DEBUG] Enviando para API:", apiUrl);
    console.log("[DEBUG] Modelo selecionado:", model);

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

        console.log("[DEBUG] Endpoint usado:", endpoint);


        const token = localStorage.getItem("token");
        console.log("[DEBUG] Token encontrado:", token ? "Sim" : "Não");

        if (!token) {
            throw new Error("Token de autenticação não encontrado. Faça login novamente.");
        }

        const headers = {};
        if (apiUrl.includes(':5236')) {

            headers['Authorization'] = `Bearer ${token}`;
            console.log("[DEBUG] Header Authorization adicionado");
        }

        console.log("[DEBUG] Fazendo requisição para:", `${apiUrl}${endpoint}`);

        const response = await fetch(`${apiUrl}${endpoint}`, {
            method: "POST",
            body: formData,
            headers: headers
        });

        console.log("[DEBUG] Status da resposta:", response.status);
        console.log("[DEBUG] Headers da resposta:", [...response.headers.entries()]);

        if (!response.ok) {
            const errorText = await response.text();
            console.error("[DEBUG] Erro na resposta:", errorText);
            throw new Error(`Erro HTTP: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        console.log("[DEBUG] Dados recebidos:", data);

        if (data.sucesso) {
            displayResults(data);
        } else {
            showError("Erro na análise: " + data.erro);
        }
    } catch (error) {
        console.error("[DEBUG] Erro completo:", error);
        showError("Erro ao conectar com API: " + error.message);
    } finally {
        showLoading(false);
    }
}


function displayResults(data) {
    console.log("[DEBUG] Exibindo resultados:", data);


    const analise = data.analise || data;
    console.log("[DEBUG] Estrutura analise:", analise);


    const emocaoDominante = analise.emocao_dominante || analise.emocao || data.emocao || "";
    document.getElementById("dominantEmotion").textContent = translateEmotion(emocaoDominante);
    console.log("[DEBUG] Emoção dominante:", emocaoDominante);


    const idade = analise.idade || data.idade || "";
    const genero = analise.genero || data.genero || "";

    document.getElementById("age").textContent = idade ? Math.round(idade) + " anos" : "-";
    document.getElementById("gender").textContent = genero === "Man" ? "Masculino" : genero === "Woman" ? "Feminino" : genero || "-";
    document.getElementById("model").textContent = data.modelo_usado || "Desconhecido";


    const emotionsGrid = document.getElementById("emotionsGrid");
    emotionsGrid.innerHTML = "";

    const emocoes = analise.emocoes || analise.emotions || data.emocoes || {};
    console.log("[DEBUG] Emoções recebidas:", emocoes);

    const sortedEmotions = Object.entries(emocoes).sort(
        (a, b) => b[1] - a[1]
    );


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
    console.log("[DEBUG] Resultados exibidos com sucesso");
}


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


async function checkAPIHealth() {
    const apiUrl = document.getElementById("apiUrl").value;
    console.log("[DEBUG] Verificando saúde da API:", apiUrl);

    try {
        const endpoint = apiUrl.includes(':5236')
            ? '/api/FacialAnalysis/health'
            : '/health';

        console.log("[DEBUG] Endpoint de saúde:", endpoint);

        const response = await fetch(`${apiUrl}${endpoint}`);
        console.log("[DEBUG] Status da resposta de saúde:", response.status);

        const data = await response.json();
        console.log("[DEBUG] Dados da resposta de saúde:", data);

        if (data.sucesso || data.status === "healthy") {
            showStatus("✅ API está online e funcionando!", "connected");
        } else {
            showStatus(
                "⚠️ API respondeu mas pode ter problemas",
                "disconnected"
            );
        }
    } catch (error) {
        console.error("[DEBUG] Erro ao verificar saúde da API:", error);
        showStatus(
            "❌ Não foi possível conectar à API",
            "disconnected"
        );
        showError(
            "Certifique-se de que a API está rodando"
        );
    }
}


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


window.addEventListener("load", () => {
    checkAPIHealth();
});