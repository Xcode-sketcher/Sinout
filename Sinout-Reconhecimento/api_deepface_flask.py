# -*- coding: utf-8 -*-

# ============================================================
# 🤖 API PYTHON DEEPFACE - O DETETIVE DE EMOÇÕES
# ============================================================
# Analogia RPG: Este é o "Mago Especialista em Leitura Mental"!
# Ele consegue olhar para uma foto e dizer:
# - Que emoção a pessoa está sentindo (feliz, triste, bravo...)
# - Quantos anos tem (aproximado)
# - Se é homem ou mulher
# - E onde está o rosto na foto
#
# Analogia Médica: É o "Especialista em Expressões Faciais"!
# Como um médico que consegue diagnosticar o estado emocional
# só de olhar o rosto do paciente.
#
# Como funciona:
# 1. Recebe uma foto (do navegador/câmera)
# 2. Usa Inteligência Artificial (DeepFace) para analisar
# 3. Retorna as emoções detectadas com percentuais
#
# IMPORTANTE: Esta API roda localmente (localhost) por segurança!
# ============================================================

from flask import Flask, request, jsonify
from flask_cors import CORS
from deepface import DeepFace  # 🧠 A "Inteligência Artificial" que detecta emoções
import cv2  # 📸 Biblioteca para processar imagens
import numpy as np  # 🔢 Matemática para trabalhar com imagens
import base64  # 🔐 Para converter imagens em texto (base64)
from datetime import datetime
from functools import wraps

import traceback  # 🐛 Para mostrar erros detalhados


app = Flask(__name__)
CORS(app)  # ✅ Permite que o frontend (C#/JavaScript) chame esta API

# ⚙️ CONFIGURAÇÕES
MODELO_PADRAO = "Facenet"  # Modelo de IA: rápido e preciso
API_KEY_SECRETA = "PYTHON_API_SECRET_KEY_2024_SINOUT_DEEPFACE_SECURE_ACCESS"  # 🔑 Senha secreta (mesma do C#)

# ============================================================
# 🛡️ MIDDLEWARE DE SEGURANÇA - O GUARDA DO PORTÃO
# ============================================================
# Analogia RPG: É como o "Guarda da Torre" que verifica crachás!
# Antes de processar qualquer pedido, verifica se tem a senha correta.
#
# Funcionamento:
# 1. Cliente (C# ou outro) envia header: X-API-Key: SENHA_SECRETA
# 2. Este decorator verifica se a senha está correta
# 3. Se sim, permite entrar. Se não, bloqueia!
#
# É como um nightclub que só deixa entrar quem tem convite!
# ============================================================
def require_api_key(f):
    """Decorator que valida X-API-Key header antes de processar requisição"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 🔍 FASE 1: Procurar a chave na requisição
        api_key = request.headers.get('X-API-Key')
        
        # ❌ VALIDAÇÃO 1: Esqueceu de enviar a chave?
        if not api_key:
            return jsonify({
                "sucesso": False,
                "erro": "API Key não fornecida",
                "mensagem": "Envie o header X-API-Key na requisição"
            }), 401  # 401 = Não autenticado
        
        # ❌ VALIDAÇÃO 2: Chave errada?
        if api_key != API_KEY_SECRETA:
            return jsonify({
                "sucesso": False,
                "erro": "API Key inválida",
                "mensagem": "A chave de API fornecida não é válida"
            }), 403  # 403 = Proibido
        
        # ✅ Chave correta! Pode entrar!
        return f(*args, **kwargs)
    
    return decorated_function

# ============================================================
# 🏠 ROTA INICIAL - A PORTA DA FRENTE
# ============================================================
# Analogia: É como a recepção de um prédio!
# Mostra informações básicas sobre o serviço.
# URL: GET http://localhost:5000/
# ============================================================
@app.route('/')
def home():
    """Rota inicial - verifica se API está rodando"""
    return jsonify({
        "status": "online",
        "mensagem": "API DeepFace Flask funcionando!",
        "versao": "2.0",
        "seguranca": "Protegido por API Key (X-API-Key header)",
        "endpoints": [
            "POST /analyze - Analisa uma imagem (REQUER X-API-Key)",
            "POST /analyze-base64 - Analisa imagem em base64 (REQUER X-API-Key)",
            "GET /models - Lista modelos disponíveis (REQUER X-API-Key)",
            "GET /health - Verifica saúde da API (REQUER X-API-Key)"
        ]
    })

# ============================================================
# 💓 HEALTH CHECK - VERIFICAÇÃO DE SAÚDE
# ============================================================
# Analogia RPG: Como verificar se o NPC ainda está vivo!
# Endpoint simples para checar se o serviço está funcionando.
# ============================================================
@app.route('/health')
@require_api_key  # 🔐 Requer senha
def health():
    """Endpoint para health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

# ============================================================
# 📚 LISTAR MODELOS - O CATÁLOGO DE MAGOS
# ============================================================
# Analogia RPG: Ver lista de "Classes de Mago" disponíveis!
# Cada modelo de IA tem vantagens/desvantagens:
# - Facenet: Rápido e preciso (RECOMENDADO)
# - VGG-Face: Muito preciso mas lento
# - OpenFace: Super rápido mas menos preciso
# ============================================================
@app.route('/models', methods=['GET'])
@require_api_key  # 🔐 Requer senha
def listar_modelos():
    """Lista os modelos disponíveis"""
    return jsonify({
        "modelos_disponiveis": [
            {"nome": "Facenet", "precisao": "97.4%", "velocidade": "rápido", "recomendado": True},
            {"nome": "VGG-Face", "precisao": "97.78%", "velocidade": "médio", "recomendado": False},
            {"nome": "Facenet512", "precisao": "98.4%", "velocidade": "lento", "recomendado": False},
            {"nome": "OpenFace", "precisao": "78.7%", "velocidade": "muito rápido", "recomendado": False},
            {"nome": "ArcFace", "precisao": "96.7%", "velocidade": "médio", "recomendado": False},
            {"nome": "Dlib", "precisao": "96.8%", "velocidade": "médio", "recomendado": False}
        ],
        "modelo_padrao": MODELO_PADRAO
    })

# ============================================================
# 🔮 ANÁLISE DE EMOÇÕES - O CORAÇÃO DA API!
# ============================================================
# Analogia RPG: A "Magia Principal" do Mago!
# Esta é a função mais importante - detecta emoções em uma foto.
#
# Analogia Médica: O "Exame Principal"!
# O paciente (foto) entra, o médico (IA) examina e dá o diagnóstico (emoções).
#
# Como usar:
# 1. Frontend tira foto da câmera
# 2. Envia arquivo de imagem via POST
# 3. Esta rota processa com DeepFace
# 4. Retorna: emoção dominante, todas as emoções com %, idade, gênero
#
# Parâmetros:
# - file: arquivo de imagem (OBRIGATÓRIO)
# - model: qual modelo de IA usar (opcional, padrão: Facenet)
# - actions: o que analisar (opcional, padrão: emoção, idade, gênero)
#
# Exemplo de retorno:
# {
#   "sucesso": true,
#   "analise": {
#     "emocao_dominante": "happy",
#     "emocoes": {
#       "happy": 85.5,
#       "neutral": 10.2,
#       "sad": 2.1,
#       "angry": 1.0,
#       "fear": 0.8,
#       "disgust": 0.3,
#       "surprise": 0.1
#     },
#     "idade": 28,
#     "genero": "Man"
#   }
# }
# ============================================================
@app.route('/analyze', methods=['POST'])
@require_api_key  # 🔐 Requer senha
def analisar_imagem():
    """
    Analisa uma imagem enviada via multipart/form-data

    Parâmetros:
        - file: arquivo de imagem (obrigatório)
        - detector: detector de faces (opcional, padrão: opencv)
        - actions: lista de análises (opcional, padrão: emotion,age,gender)

    Retorna:
        JSON com análise da face
    """
    try:
        # ❌ VALIDAÇÃO 1: Arquivo enviado?
        if 'file' not in request.files:
            return jsonify({
                "sucesso": False,
                "erro": "Nenhum arquivo enviado. Use o campo 'file'"
            }), 400

        file = request.files['file']

        # ❌ VALIDAÇÃO 2: Nome do arquivo vazio?
        if file.filename == '':
            return jsonify({
                "sucesso": False,
                "erro": "Nome do arquivo vazio"
            }), 400

        # ⚙️ FASE 1: LER PARÂMETROS OPCIONAIS
        # Nota: 'model' é ignorado pois analyze() usa modelos fixos para atributos.
        # Usamos 'detector' para o backend de detecção facial.
        detector = request.form.get('detector', 'opencv')
        actions_str = request.form.get('actions', 'emotion,age,gender')
        actions = [a.strip() for a in actions_str.split(',')]

        # 📸 FASE 2: CONVERTER ARQUIVO EM IMAGEM
        # Analogia: Como revelar uma foto analógica!
        file_bytes = np.frombuffer(file.read(), np.uint8)  # Ler bytes
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)   # Decodificar imagem

        # ❌ VALIDAÇÃO 3: Imagem válida?
        if img is None:
            return jsonify({
                "sucesso": False,
                "erro": "Não foi possível decodificar a imagem"
            }), 400

        # 🧠 FASE 3: MAGIA! Analisar com DeepFace
        # Analogia: O mago lançando o feitiço de "Leitura Mental"!
        resultado = DeepFace.analyze(
            img,
            actions=actions,              # O que analisar: emoção, idade, gênero
            enforce_detection=False,      # Não falhar se não detectar rosto perfeitamente
            detector_backend=detector,    # Detector de rostos (opencv é padrão e rápido)
            silent=True                   # Não mostrar logs no console
        )

        # 📊 FASE 4: PROCESSAR RESULTADO
        # DeepFace retorna lista se detectar múltiplas faces, pegamos a primeira
        if isinstance(resultado, list):
            resultado = resultado[0]

        # 🎁 FASE 5: PREPARAR RESPOSTA BONITA
        # Organizar os dados de forma clara para o frontend
        resposta = {
            "sucesso": True,
            "timestamp": datetime.now().isoformat(),  # Quando foi analisado
            "detector_usado": detector,
            "analise": {
                "emocao_dominante": resultado.get('dominant_emotion'),  # Ex: "happy"
                "emocoes": resultado.get('emotion', {}),                 # Ex: {"happy": 85.5, "sad": 10.2, ...}
                "idade": resultado.get('age'),                           # Ex: 28
                "genero": resultado.get('dominant_gender') or resultado.get('gender'),  # Ex: "Man" ou "Woman"
                "raca_dominante": resultado.get('dominant_race'),        # Ex: "white", "asian", etc
                "regiao_face": resultado.get('region', {})               # Coordenadas do rosto na imagem
            },
            "dados_completos": resultado  # Dados brutos completos (para debug)
        }

        return jsonify(resposta), 200  # ✅ Sucesso!

    except Exception as e:
        # 💥 TRATAMENTO DE ERRO: Algo deu errado!
        return jsonify({
            "sucesso": False,
            "erro": str(e),
            "tipo_erro": type(e).__name__,
            "traceback": traceback.format_exc()  # Rastreamento completo do erro
        }), 500

@app.route('/analyze-base64', methods=['POST'])
@require_api_key
def analisar_base64():
    """
    Analisa uma imagem enviada em base64

    JSON esperado:
    {
        "image_base64": "...",
        "model": "Facenet" (opcional),
        "actions": ["emotion", "age", "gender"] (opcional)
    }
    """
    try:
        data = request.get_json()

        if not data or 'image_base64' not in data:
            return jsonify({
                "sucesso": False,
                "erro": "Campo 'image_base64' é obrigatório no JSON"
            }), 400

        # Decodificar base64
        image_base64 = data['image_base64']

        # Remover prefixo se existir (data:image/png;base64,)
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]

        img_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({
                "sucesso": False,
                "erro": "Não foi possível decodificar a imagem base64"
            }), 400

        # Ler parâmetros opcionais
        detector = data.get('detector', 'opencv')
        actions = data.get('actions', ['emotion', 'age', 'gender'])

        # Analisar com DeepFace
        # Nota: detector_backend usa opencv, ssd, dlib, mtcnn, etc (não Facenet)
        resultado = DeepFace.analyze(
            img,
            actions=actions,
            enforce_detection=False,
            detector_backend=detector,  # Usar detector padrão
            silent=True
        )

        if isinstance(resultado, list):
            resultado = resultado[0]

        # Preparar resposta estruturada
        resposta = {
            "sucesso": True,
            "timestamp": datetime.now().isoformat(),
            "detector_usado": detector,
            "analise": {
                "emocao_dominante": resultado.get('dominant_emotion'),
                "emocoes": resultado.get('emotion', {}),
                "idade": resultado.get('age'),
                "genero": resultado.get('dominant_gender') or resultado.get('gender'),
                "raca_dominante": resultado.get('dominant_race'),
                "regiao_face": resultado.get('region', {})
            },
            "dados_completos": resultado
        }

        return jsonify(resposta), 200

    except Exception as e:
        return jsonify({
            "sucesso": False,
            "erro": str(e),
            "tipo_erro": type(e).__name__,
            "traceback": traceback.format_exc()
        }), 500

@app.route('/analyze-multiple', methods=['POST'])
def analisar_multiplas():
    """
    Analisa múltiplas faces em uma imagem
    Detecta todas as faces e retorna análise de cada uma
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                "sucesso": False,
                "erro": "Nenhum arquivo enviado"
            }), 400

        file = request.files['file']
        detector = request.form.get('detector', 'opencv')

        # Ler imagem
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({
                "sucesso": False,
                "erro": "Imagem inválida"
            }), 400

        # Detectar faces
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

        resultados = []

        for i, (x, y, w, h) in enumerate(faces):
            face_region = img[y:y+h, x:x+w]

            # Analisar cada face
            resultado = DeepFace.analyze(
                face_region,
                actions=['emotion', 'age', 'gender'],
                enforce_detection=False,
                detector_backend=detector,
                silent=True
            )

            if isinstance(resultado, list):
                resultado = resultado[0]

            resultados.append({
                "face_id": i,
                "coordenadas": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                "emocao_dominante": resultado.get('dominant_emotion'),
                "emocoes": resultado.get('emotion', {}),
                "idade": resultado.get('age'),
                "genero": resultado.get('dominant_gender') or resultado.get('gender')
            })

        return jsonify({
            "sucesso": True,
            "timestamp": datetime.now().isoformat(),
            "detector_usado": detector,
            "total_faces": len(resultados),
            "faces": resultados
        }), 200

    except Exception as e:
        return jsonify({
            "sucesso": False,
            "erro": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.errorhandler(404)
def nao_encontrado(e):
    return jsonify({
        "sucesso": False,
        "erro": "Endpoint não encontrado",
        "endpoints_disponiveis": ["/", "/analyze", "/analyze-base64", "/analyze-multiple", "/models", "/health"]
    }), 404

@app.errorhandler(500)
def erro_interno(e):
    return jsonify({
        "sucesso": False,
        "erro": "Erro interno do servidor",
        "detalhes": str(e)
    }), 500

if __name__ == '__main__':
    print("="*60)
    print("🚀 API DeepFace Flask - Modo Interno")
    print("="*60)
    print("✅ Servidor iniciando...")
    print("📍 URL: http://localhost:5000")
    print("📚 Endpoints disponíveis:")
    print("   GET  /           - Informações da API")
    print("   GET  /health     - Health check")
    print("   GET  /models     - Lista modelos")
    print("   POST /analyze    - Analisa imagem (multipart)")
    print("   POST /analyze-base64 - Analisa imagem (base64)")
    print("   POST /analyze-multiple - Múltiplas faces")
    print("="*60)
    print("\n⚠️  Esta API deve rodar APENAS internamente!")
    print("   Para produção, use: flask run --host=127.0.0.1")
    print("\n")

    # Rodar apenas em localhost (interno)
    app.run(host='127.0.0.1', port=5000, debug=True)
