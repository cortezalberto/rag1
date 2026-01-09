# Guia de Ejecucion RAG-Restaurante

Este documento contiene los comandos necesarios para ejecutar el proyecto desde la carpeta `rag/`.

## Requisitos Previos

- Docker Desktop instalado y ejecutandose
- Python 3.10+ instalado
- Ollama instalado

## 1. Configuracion Inicial (solo la primera vez)

### Crear y activar entorno virtual

```bash
# Desde la raiz del repositorio
cd rag

# Crear entorno virtual
python -m venv ../.venv

# Activar entorno virtual
# Windows PowerShell:
..\.venv\Scripts\Activate.ps1

# Windows CMD:
..\.venv\Scripts\activate.bat

# Linux/Mac:
source ../.venv/bin/activate
```

### Instalar dependencias

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Para desarrollo
```

### Descargar modelos de Ollama

```bash
ollama pull nomic-embed-text    # Modelo de embeddings (requerido)
ollama pull llama3.2:1b         # Modelo de chat (default)
```

## 2. Iniciar Servicios

### Iniciar base de datos PostgreSQL

```bash
cd rag
docker compose up -d
```

Esto inicia PostgreSQL 16 con pgvector en el puerto 5434.

### Verificar que el contenedor esta corriendo

```bash
docker ps
```

Deberia mostrar el contenedor `menu_rag_db` en estado "Up".

## 3. Ejecutar la Aplicacion

### Modo desarrollo (con auto-reload)

```bash
cd rag
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Modo produccion

```bash
cd rag
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 4. Verificar el Sistema

### Health check via terminal

```bash
curl http://localhost:8000/health
```

### Acceder a la documentacion API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Usar la interfaz web

Abrir el archivo `rag/index.html` en el navegador.

## 5. Cargar Datos Iniciales

### Cargar platos de ejemplo

```bash
curl -X POST http://localhost:8000/seed
```

### Generar embeddings

```bash
curl -X POST http://localhost:8000/index
```

Este proceso puede tomar 1-2 minutos.

## 6. Ejecutar Tests

```bash
cd rag

# Todos los tests
pytest

# Solo tests unitarios
pytest tests/unit/

# Test especifico
pytest tests/unit/test_text_service.py

# Con cobertura
pytest --cov=src
```

## 7. Linting y Type Checking

```bash
cd rag

# Verificar codigo
ruff check src/

# Auto-fix issues
ruff check src/ --fix

# Type checking
mypy src/
```

## 8. Detener Servicios

### Detener la aplicacion

Presionar `Ctrl+C` en la terminal donde corre uvicorn.

### Detener base de datos (mantener datos)

```bash
cd rag
docker compose down
```

### Detener y eliminar datos

```bash
cd rag
docker compose down -v
```

## 9. Comandos Utiles de Docker

```bash
# Ver logs del contenedor
docker logs menu_rag_db

# Acceder a PostgreSQL
docker exec -it menu_rag_db psql -U postgres -d menu_rag

# Reiniciar contenedor
docker compose restart
```

## 10. Estructura de Carpetas

```
rag/
├── app.py               # Entry point FastAPI
├── docker-compose.yml   # Configuracion PostgreSQL
├── requirements.txt     # Dependencias Python
├── .env                 # Variables de entorno
├── src/                 # Codigo fuente
│   ├── api/            # Endpoints HTTP
│   ├── config/         # Configuracion
│   ├── core/           # Constantes y excepciones
│   ├── models/         # Entidades SQLAlchemy
│   ├── repositories/   # Acceso a datos
│   ├── schemas/        # Pydantic models
│   └── services/       # Logica de negocio
├── tests/              # Tests
├── data/               # Datos de seed
└── index.html          # UI web
```

## Troubleshooting

### Error: "connection refused" a la base de datos

1. Verificar que Docker este corriendo: `docker ps`
2. Verificar el puerto: debe ser 5434, no 5432
3. Reiniciar el contenedor: `docker compose restart`

### Error: "model not found" en Ollama

```bash
ollama list                    # Ver modelos instalados
ollama pull nomic-embed-text   # Descargar modelo faltante
```

### Error: "ReadTimeout" al hacer consultas

El modelo es muy pesado para el hardware. Cambiar a un modelo mas liviano en `.env`:

```
CHAT_MODEL=llama3.2:1b
```
