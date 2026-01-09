# 🥘 Menu RAG - Sistema de Consultas sobre Menú con IA

Sistema de Retrieval-Augmented Generation (RAG) para responder preguntas sobre un menú de restaurante, con énfasis en información sobre alérgenos, ingredientes y características de los platos.

## 📋 Características

- **Base de Conocimientos Vectorial**: Utiliza pgvector para búsqueda semántica eficiente
- **IA Conversacional**: Powered by Ollama con modelos de lenguaje locales
- **Respuestas Contextuales**: RAG combina búsqueda vectorial con generación de lenguaje natural
- **Gestión de Alérgenos**: Énfasis especial en información crítica de seguridad alimentaria
- **Interfaz Web Simple**: UI en HTML/JavaScript vanilla para consultas interactivas
- **API RESTful**: FastAPI con endpoints documentados automáticamente

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.10+ con FastAPI
- **Base de Datos**: PostgreSQL 16 con extensión pgvector
- **Embeddings**: Ollama (nomic-embed-text)
- **LLM**: Ollama (llama3.2:1b o modelos compatibles)
- **ORM**: SQLAlchemy
- **Contenedores**: Docker + Docker Compose

## 📦 Requisitos Previos

### Software Requerido

1. **Docker Desktop** (para Windows)
   - [Descargar Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Verificar: `docker --version` y `docker compose version`

2. **Python 3.10 o superior**
   - [Descargar Python](https://www.python.org/downloads/)
   - Verificar: `python --version`

3. **Ollama**
   - [Descargar Ollama](https://ollama.ai/download)
   - Verificar: `ollama --version`

### Hardware Recomendado

- **RAM**: Mínimo 8GB (16GB recomendado para modelos más grandes)
- **CPU**: Procesador moderno con al menos 4 núcleos
- **Disco**: 5GB libres (para modelos de Ollama)

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone <url-del-repo>
cd menu-rag
```

### 2. Configurar Python

#### Crear Entorno Virtual

```powershell
python -m venv .venv
```

#### Activar Entorno Virtual

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

#### Instalar Dependencias

```powershell
pip install -r requirements.txt
```

### 3. Configurar Base de Datos

#### Iniciar PostgreSQL con Docker

```powershell
docker compose up -d
```

Esto iniciará PostgreSQL 16 con pgvector en el puerto **5434**.

> **⚠️ Nota Importante**: Si tienes PostgreSQL instalado localmente en Windows, puede estar usando el puerto 5433. Por eso este proyecto usa el puerto 5434 para evitar conflictos.

#### Inicialización de Base de Datos

La base de datos se inicializa automáticamente al iniciar la aplicación por primera vez. Esto incluye:
- Creación de la extensión pgvector
- Creación de todas las tablas
- Creación de índices para búsqueda vectorial

### 4. Configurar Ollama

#### Descargar Modelos Necesarios

```powershell
# Modelo de embeddings (requerido, ~274MB)
ollama pull nomic-embed-text

# Modelo de chat (elige UNO según tu hardware)
# Opción 1: Liviano - Recomendado para 8GB RAM (~1.3GB)
ollama pull llama3.2:1b

# Opción 2: Equilibrado - Requiere 16GB RAM (~3GB)
ollama pull llama3.2:3b

# Opción 3: Potente - Requiere 32GB RAM (~4.7GB)
ollama pull qwen2.5:7b
```

#### Verificar Instalación

```powershell
ollama list
```

Deberías ver los modelos descargados listados.

### 5. Configuración (Opcional)

El archivo [`.env`](.env) contiene la configuración por defecto:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5434/menu_rag
OLLAMA_URL=http://localhost:11434
EMBED_MODEL=nomic-embed-text
CHAT_MODEL=llama3.2:1b
```

Puedes modificarlo según tus necesidades, especialmente `CHAT_MODEL` si descargaste un modelo diferente.

## ▶️ Ejecución

### 1. Iniciar Servicios

#### En una terminal: Iniciar Base de Datos

```powershell
docker compose up -d
```

#### En otra terminal: Iniciar API

```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Iniciar servidor FastAPI
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Deberías ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### 2. Verificar Sistema

Abre tu navegador y accede a:
- **API Docs**: http://localhost:8000/docs (Swagger UI interactivo)
- **Health Check**: http://localhost:8000/health

### 3. Usar la Interfaz Web

1. Abre el archivo [`index.html`](index.html) directamente en tu navegador
2. Sigue estos pasos en orden:

#### a) Health Check
Haz clic en **"Health Check"** para verificar que todo esté conectado:
- ✅ DB: 10 platos
- ✅ Embeddings: 0 (inicial)
- ✅ Ollama: Conectado

#### b) Cargar Datos
Haz clic en **"1) Seed Cargar Platos"** para cargar los 10 platos de ejemplo en la base de datos.

#### c) Indexar Embeddings
Haz clic en **"2) Index Embeddings"** y espera 1-2 minutos. Este proceso:
- Genera vectores para cada plato usando Ollama
- Los guarda en PostgreSQL para búsqueda semántica

#### d) Hacer Preguntas
Ahora puedes hacer preguntas como:
- "¿Tiene maní?"
- "¿Es picante?"
- "¿Contiene lácteos?"
- "¿Es apto para celíacos?"
- "¿Cuáles son los ingredientes?"

## 🔧 Solución de Problemas

### Error: "connection timeout" o "no existe la base de datos"

**Causa**: PostgreSQL local de Windows está interceptando las conexiones en el puerto 5433.

**Solución**: El proyecto ya usa el puerto 5434 para evitar esto. Verifica que el archivo `docker-compose.yml` y `app.py` usen el puerto correcto:

```yaml
# docker-compose.yml
ports:
  - "5434:5432"  # ← Puerto 5434
```

### Error: "model not found" en Ollama

**Causa**: El modelo especificado en `CHAT_MODEL` no está descargado.

**Solución**:
```powershell
# Ver modelos instalados
ollama list

# Descargar el modelo que necesitas
ollama pull llama3.2:1b
```

### Error: "ReadTimeout" al hacer preguntas

**Causa**: El modelo es muy pesado para tu hardware.

**Solución**: Cambia a un modelo más liviano en [`app.py`](app.py):

```python
CHAT_MODEL = "llama3.2:1b"  # En lugar de qwen2.5:7b
```

### Error: "Import psycopg could not be resolved"

**Causa**: Pylance no está usando el entorno virtual correcto.

**Solución**:
1. En VS Code, presiona `Ctrl+Shift+P`
2. Escribe "Python: Select Interpreter"
3. Selecciona el intérprete de `.venv`

### Base de Datos se Pierde al Reiniciar

**Causa**: Docker Compose crea un volumen persistente, pero si haces `docker compose down -v` elimina los datos.

**Solución**: Usa solo `docker compose down` (sin `-v`) para mantener los datos.

Para recrear todo desde cero:
```powershell
docker compose down -v
docker compose up -d
# Reiniciar la app - las tablas se crean automáticamente
uvicorn app:app --reload
```

## 📚 Arquitectura del Sistema

### Flujo de Datos RAG

1. **Indexación** (una vez):
   ```
   Fichas de Platos → Chunking → Ollama (embeddings) → pgvector
   ```

2. **Consulta** (cada pregunta):
   ```
   Pregunta Usuario → Embedding → Búsqueda Vectorial → 
   Top K Chunks → Contexto + Prompt → Ollama (LLM) → Respuesta
   ```

### Estructura de la Base de Datos

- **`dish`**: Platos del menú
- **`kb_chunk`**: Fragmentos de texto de las fichas técnicas
- **`kb_embedding`**: Vectores de embeddings (768 dimensiones)
- **`chat_turn`**: Historial de conversaciones
- **`rag_trace`**: Trazabilidad de chunks usados por consulta

## 🧪 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado del sistema |
| GET | `/dishes` | Lista todos los platos |
| POST | `/seed` | Carga 10 platos de ejemplo |
| POST | `/index` | Genera embeddings para todos los platos |
| POST | `/chat` | Realiza una consulta sobre el menú |

Ver documentación completa en: http://localhost:8000/docs

## 📝 Comandos Útiles

### Docker

```powershell
# Ver logs del contenedor
docker logs menu_rag_db

# Acceder a PostgreSQL
docker exec -it menu_rag_db psql -U postgres -d menu_rag

# Reiniciar contenedor
docker compose restart

# Detener todo
docker compose down
```

### Base de Datos

```powershell
# Desde dentro del contenedor
docker exec -it menu_rag_db psql -U postgres -d menu_rag

# Listar tablas
\dt

# Ver embeddings
SELECT COUNT(*) FROM kb_embedding;

# Salir
\q
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🙏 Agradecimientos

- [Ollama](https://ollama.ai/) por democratizar el acceso a LLMs locales
- [pgvector](https://github.com/pgvector/pgvector) por la extensión de vectores en PostgreSQL
- [FastAPI](https://fastapi.tiangolo.com/) por el excelente framework web

---

**¿Necesitas ayuda?** Abre un issue en el repositorio con detalles de tu problema y el output de:
```powershell
docker ps
ollama list
python --version
```
