from flask import Flask, request, jsonify
from flask_cors import CORS
from deepface import DeepFace
import cv2
import numpy as np
import base64
from datetime import datetime
from functools import wraps
import os
import traceback
import logging
import json

app = Flask(__name__)
CORS(app)


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def convert_numpy_types(obj):
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

app.json.encoder = NumpyEncoder
MODELO_PADRAO = "Facenet"
API_KEY_SECRETA = os.environ.get(
    'PYTHON_API_KEY',
    'PYTHON_API_SECRET_KEY_2024_SINOUT_DEEPFACE_SECURE_ACCESS'
)

# Definir ambiente da aplicação: `development` ou `production`
APP_ENV = os.environ.get('APP_ENV', os.environ.get('FLASK_ENV', 'production'))

# Configurar logger: em `development`
if APP_ENV.lower() == 'development':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('Sinout-Reconhecimento')
def require_api_key(f):
    """Decorator que valida o header X-API-Key antes de processar a requisição.

    Em caso de API Key não fornecida, retorna 401. Em caso inválido, retorna 403.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                "sucesso": False,
                "erro": "API Key não fornecida",
                "mensagem": "Envie o header X-API-Key na requisição"
            }), 401
        if api_key != API_KEY_SECRETA:
            logger.warning('Attempt to access without valid API key')
            return jsonify({
                "sucesso": False,
                "erro": "API Key inválida",
                "mensagem": "A chave de API fornecida não é válida"
            }), 403
        return f(*args, **kwargs)
    return decorated_function
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
@app.route('/health')
def health():
    """Endpoint para health check (sem autenticação)"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })
@app.route('/models', methods=['GET'])
@require_api_key
def listar_modelos():
    """Lista os modelos disponíveis para análise facial.

    Retorna um JSON com os modelos e o modelo padrão.
    """
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
@app.route('/analyze', methods=['POST'])
@require_api_key
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
        if 'file' not in request.files:
            return jsonify({
                "sucesso": False,
                "erro": "Nenhum arquivo enviado. Use o campo 'file'"
            }), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "sucesso": False,
                "erro": "Nome do arquivo vazio"
            }), 400
        detector = request.form.get('detector', 'opencv')
        actions_str = request.form.get('actions', 'emotion,age,gender')
        actions = [a.strip() for a in actions_str.split(',')]
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({
                "sucesso": False,
                "erro": "Não foi possível decodificar a imagem"
            }), 400
        resultado = DeepFace.analyze(
            img,
            actions=actions,
            enforce_detection=False,
            detector_backend=detector,
            silent=True
        )
        if isinstance(resultado, list):
            resultado = resultado[0]
        
        resultado = convert_numpy_types(resultado)
        
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
        # Registrar exceção internamente, sem expor detalhes em produção
        logger.exception('Erro ao processar /analyze')
        if APP_ENV.lower() == 'development':
            return jsonify({
                "sucesso": False,
                "erro": str(e),
                "tipo_erro": type(e).__name__,
                "traceback": traceback.format_exc()
            }), 500
        # Em produção retornamos uma mensagem genérica
        return jsonify({
            "sucesso": False,
            "erro": "Erro interno ao processar a imagem"
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
        image_base64 = data['image_base64']
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
        detector = data.get('detector', 'opencv')
        actions = data.get('actions', ['emotion', 'age', 'gender'])
        resultado = DeepFace.analyze(
            img,
            actions=actions,
            enforce_detection=False,
            detector_backend=detector,
            silent=True
        )
        if isinstance(resultado, list):
            resultado = resultado[0]
        
        resultado = convert_numpy_types(resultado)
        
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
        logger.exception('Erro ao processar /analyze-base64')
        if APP_ENV.lower() == 'development':
            return jsonify({
                "sucesso": False,
                "erro": str(e),
                "tipo_erro": type(e).__name__,
                "traceback": traceback.format_exc()
            }), 500
        return jsonify({
            "sucesso": False,
            "erro": "Erro interno ao processar imagem base64"
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
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({
                "sucesso": False,
                "erro": "Imagem inválida"
            }), 400
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
        resultados = []
        for i, (x, y, w, h) in enumerate(faces):
            face_region = img[y:y+h, x:x+w]
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
        logger.exception('Erro ao processar /analyze-multiple')
        if APP_ENV.lower() == 'development':
            return jsonify({
                "sucesso": False,
                "erro": str(e),
                "traceback": traceback.format_exc()
            }), 500
        return jsonify({
            "sucesso": False,
            "erro": "Erro interno ao processar múltiplas faces"
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
    # Gerência central de erros: registra internamente e evita retorno de detalhes em produção
    logger.exception('Erro interno exception handler')
    if APP_ENV.lower() == 'development':
        return jsonify({
            "sucesso": False,
            "erro": "Erro interno do servidor",
            "detalhes": str(e)
        }), 500
    return jsonify({
        "sucesso": False,
        "erro": "Erro interno do servidor"
    }), 500
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 