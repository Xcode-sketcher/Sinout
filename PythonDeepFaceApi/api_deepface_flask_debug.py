# -*- coding: utf-8 -*-
"""
API Flask para Análise Facial com DeepFace - Versão com DEBUG
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from deepface import DeepFace
import cv2
import numpy as np
import base64
from datetime import datetime
import traceback
import logging

app = Flask(__name__)
CORS(app)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MODELO_PADRAO = "Facenet"

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "mensagem": "API DeepFace Flask funcionando!",
        "versao": "1.0"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analisar_imagem():
    """
    Analisa uma imagem enviada via multipart/form-data
    """
    logger.info("=== NOVA REQUISIÇÃO /analyze ===")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Files: {request.files.keys()}")
    logger.info(f"Form: {request.form.keys()}")
    
    try:
        # Validar arquivo
        if 'file' not in request.files:
            logger.warning("Erro: Campo 'file' não encontrado")
            logger.warning(f"Campos disponíveis: {request.files.keys()}")
            return jsonify({
                "sucesso": False,
                "erro": "Campo 'file' não encontrado. Campos disponíveis: " + str(list(request.files.keys()))
            }), 400
        
        file = request.files['file']
        logger.info(f"Arquivo recebido: {file.filename}, Tamanho: {file.content_length} bytes")
        
        if file.filename == '':
            logger.warning("Erro: Nome do arquivo vazio")
            return jsonify({
                "sucesso": False,
                "erro": "Nome do arquivo vazio"
            }), 400
        
        # Ler parâmetros
        modelo = request.form.get('model', MODELO_PADRAO)
        logger.info(f"Modelo: {modelo}")
        
        # Ler imagem
        logger.info("Decodificando imagem...")
        file_bytes = np.frombuffer(file.read(), np.uint8)
        logger.info(f"Bytes lidos: {len(file_bytes)}")
        
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if img is None:
            logger.error("Erro: Não foi possível decodificar a imagem")
            return jsonify({
                "sucesso": False,
                "erro": "Não foi possível decodificar a imagem. Arquivo corrompido ou formato inválido."
            }), 400
        
        logger.info(f"Imagem decodificada com sucesso! Dimensões: {img.shape}")
        
        # Analisar com DeepFace
        logger.info("Iniciando análise...")
        resultado = DeepFace.analyze(
            img,
            actions=['emotion', 'age', 'gender'],
            enforce_detection=False,
            silent=True
        )
        
        logger.info("Análise concluída com sucesso!")
        
        if isinstance(resultado, list):
            resultado = resultado[0]
        
        resposta = {
            "sucesso": True,
            "timestamp": datetime.now().isoformat(),
            "modelo_usado": modelo,
            "analise": {
                "emocao_dominante": resultado.get('dominant_emotion'),
                "emocoes": resultado.get('emotion', {}),
                "idade": resultado.get('age'),
                "genero": resultado.get('dominant_gender') or resultado.get('gender'),
                "regiao_face": resultado.get('region', {})
            }
        }
        
        logger.info(f"Resposta enviada: {resposta['analise']['emocao_dominante']}")
        return jsonify(resposta), 200
    
    except Exception as e:
        logger.error(f"ERRO NA ANÁLISE: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "sucesso": False,
            "erro": str(e),
            "tipo_erro": type(e).__name__,
            "traceback": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    print("="*60)
    print("🚀 API DeepFace Flask - COM DEBUG")
    print("="*60)
    print("📍 URL: http://localhost:5000")
    print("✅ Logging ativado - veja mensagens detalhadas aqui!")
    print("="*60)
    app.run(host='127.0.0.1', port=5000, debug=True)
# -*- coding: utf-8 -*-
"""
API Flask para Análise Facial com DeepFace - Versão com DEBUG
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from deepface import DeepFace
import cv2
import numpy as np
import base64
from datetime import datetime
import traceback
import logging

app = Flask(__name__)
CORS(app)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MODELO_PADRAO = "Facenet"

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "mensagem": "API DeepFace Flask funcionando!",
        "versao": "1.0"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analisar_imagem():
    """
    Analisa uma imagem enviada via multipart/form-data
    """
    logger.info("=== NOVA REQUISIÇÃO /analyze ===")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Files: {request.files.keys()}")
    logger.info(f"Form: {request.form.keys()}")
    
    try:
        # Validar arquivo
        if 'file' not in request.files:
            logger.warning("Erro: Campo 'file' não encontrado")
            logger.warning(f"Campos disponíveis: {request.files.keys()}")
            return jsonify({
                "sucesso": False,
                "erro": "Campo 'file' não encontrado. Campos disponíveis: " + str(list(request.files.keys()))
            }), 400
        
        file = request.files['file']
        logger.info(f"Arquivo recebido: {file.filename}, Tamanho: {file.content_length} bytes")
        
        if file.filename == '':
            logger.warning("Erro: Nome do arquivo vazio")
            return jsonify({
                "sucesso": False,
                "erro": "Nome do arquivo vazio"
            }), 400
        
        # Ler parâmetros
        modelo = request.form.get('model', MODELO_PADRAO)
        logger.info(f"Modelo: {modelo}")
        
        # Ler imagem
        logger.info("Decodificando imagem...")
        file_bytes = np.frombuffer(file.read(), np.uint8)
        logger.info(f"Bytes lidos: {len(file_bytes)}")
        
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if img is None:
            logger.error("Erro: Não foi possível decodificar a imagem")
            return jsonify({
                "sucesso": False,
                "erro": "Não foi possível decodificar a imagem. Arquivo corrompido ou formato inválido."
            }), 400
        
        logger.info(f"Imagem decodificada com sucesso! Dimensões: {img.shape}")
        
        # Analisar com DeepFace
        logger.info(f"Iniciando análise com modelo {modelo}...")
        resultado = DeepFace.analyze(
            img,
            actions=['emotion', 'age', 'gender'],
            enforce_detection=False,
            detector_backend=modelo,
            silent=True
        )
        
        logger.info("Análise concluída com sucesso!")
        
        if isinstance(resultado, list):
            resultado = resultado[0]
        
        resposta = {
            "sucesso": True,
            "timestamp": datetime.now().isoformat(),
            "modelo_usado": modelo,
            "analise": {
                "emocao_dominante": resultado.get('dominant_emotion'),
                "emocoes": resultado.get('emotion', {}),
                "idade": resultado.get('age'),
                "genero": resultado.get('dominant_gender') or resultado.get('gender'),
                "regiao_face": resultado.get('region', {})
            }
        }
        
        logger.info(f"Resposta enviada: {resposta['analise']['emocao_dominante']}")
        return jsonify(resposta), 200
    
    except Exception as e:
        logger.error(f"ERRO NA ANÁLISE: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "sucesso": False,
            "erro": str(e),
            "tipo_erro": type(e).__name__,
            "traceback": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    print("="*60)
    print("🚀 API DeepFace Flask - COM DEBUG")
    print("="*60)
    print("📍 URL: http://localhost:5000")
    print("✅ Logging ativado - veja mensagens detalhadas aqui!")
    print("="*60)
    app.run(host='127.0.0.1', port=5000, debug=True)
