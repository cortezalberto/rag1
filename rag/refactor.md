# Documento de Arquitectura: RAG-Restaurante

## Informe Técnico de Refactorización y Diseño del Sistema

**Autor**: Arquitecto de Software
**Fecha**: Enero 2026
**Versión**: 1.0.0

---

## 1. Resumen Ejecutivo

El presente documento describe en detalle la arquitectura del sistema RAG-Restaurante, un sistema de consultas inteligentes sobre menús de restaurante basado en tecnología de Retrieval-Augmented Generation (RAG). Este informe explica las decisiones arquitectónicas tomadas durante el proceso de refactorización, los patrones de diseño implementados, las ventajas de la nueva estructura modular, y proporciona una guía completa para entender, mantener y extender el sistema.

El proyecto ha sido transformado desde un archivo monolítico de 575 líneas de código hacia una arquitectura por capas bien definida, siguiendo los principios SOLID, patrones de diseño empresariales y las mejores prácticas de desarrollo de software moderno.

---

## 2. Contexto y Problemática Inicial

### 2.1 Estado Original del Proyecto

Antes de la refactorización, el proyecto consistía principalmente en un único archivo `app.py` que contenía toda la lógica de la aplicación: endpoints de la API, modelos de base de datos, lógica de negocio, comunicación con servicios externos, procesamiento de texto y generación de prompts. Esta estructura presentaba varios problemas significativos:

El archivo monolítico hacía extremadamente difícil la navegación y comprensión del código. Un desarrollador nuevo necesitaría considerable tiempo para entender qué hacía cada sección del código y cómo se relacionaban entre sí las diferentes funcionalidades. La falta de separación de responsabilidades significaba que cualquier cambio, por pequeño que fuera, podría tener efectos inesperados en otras partes del sistema.

La testabilidad del código era prácticamente nula. Sin una clara separación entre capas, era imposible escribir pruebas unitarias efectivas que aislaran comportamientos específicos. Cualquier prueba requeriría configurar toda la infraestructura del sistema, incluyendo la base de datos y el servicio de Ollama.

La reutilización de código era limitada. Funciones que podrían ser útiles en diferentes contextos estaban entrelazadas con lógica específica de endpoints, haciendo imposible su uso independiente.

### 2.2 Objetivos de la Refactorización

La refactorización se planteó con objetivos claros y medibles. En primer lugar, lograr una separación completa de responsabilidades donde cada módulo tuviera una única razón para cambiar. En segundo lugar, facilitar la escritura de pruebas automatizadas tanto unitarias como de integración. En tercer lugar, permitir que el sistema escale horizontalmente sin requerir cambios arquitectónicos significativos. Finalmente, crear una base de código que nuevos desarrolladores pudieran entender rápidamente.

---

## 3. Arquitectura por Capas Implementada

### 3.1 Visión General de las Capas

La nueva arquitectura organiza el código en capas bien definidas, donde cada capa tiene responsabilidades específicas y solo puede comunicarse con las capas adyacentes. Esta organización sigue el principio de inversión de dependencias, donde las capas superiores dependen de abstracciones definidas por las capas inferiores.

La capa de presentación, implementada en el directorio `src/api/`, se encarga exclusivamente de recibir peticiones HTTP, validar la entrada de datos mediante esquemas Pydantic, invocar a los servicios correspondientes y formatear las respuestas. Esta capa no contiene lógica de negocio; su única responsabilidad es actuar como interfaz entre el mundo exterior y el núcleo de la aplicación.

La capa de servicios, ubicada en `src/services/`, contiene toda la lógica de negocio del sistema. Aquí reside la inteligencia de la aplicación: el procesamiento de texto, la orquestación del pipeline RAG, la comunicación con Ollama y la toma de decisiones basadas en niveles de confianza. Cada servicio tiene una responsabilidad específica y bien acotada.

La capa de repositorios, en `src/repositories/`, abstrae completamente el acceso a datos. Los repositorios proporcionan una interfaz limpia para realizar operaciones de persistencia sin exponer detalles de implementación como consultas SQL o la estructura de las tablas. Esta abstracción permite cambiar la tecnología de almacenamiento sin afectar a las capas superiores.

La capa de modelos, en `src/models/`, define las entidades del dominio mediante SQLAlchemy ORM. Estos modelos representan la estructura de datos persistente y contienen las relaciones entre entidades.

### 3.2 Estructura de Directorios

La estructura final del proyecto refleja la arquitectura por capas descrita:

```
RAG-Restaurante/
├── src/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routers/
│   │       ├── health.py
│   │       ├── dishes.py
│   │       ├── chat.py
│   │       └── admin.py
│   ├── config/
│   │   └── settings.py
│   ├── core/
│   │   ├── constants.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── database.py
│   │   └── entities.py
│   ├── repositories/
│   │   ├── dish_repository.py
│   │   ├── chunk_repository.py
│   │   ├── embedding_repository.py
│   │   └── chat_repository.py
│   ├── schemas/
│   │   ├── chat.py
│   │   ├── dish.py
│   │   └── common.py
│   └── services/
│       ├── chat_service.py
│       ├── retrieval_service.py
│       ├── ollama_service.py
│       ├── text_service.py
│       ├── prompt_service.py
│       └── seed_service.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── data/
│   └── seed_dishes.py
├── app.py
├── docker-compose.yml
└── requirements.txt
```

Esta organización permite a cualquier desarrollador localizar rápidamente el código relacionado con una funcionalidad específica. Si necesita modificar cómo se procesan las consultas de chat, sabe que debe buscar en `src/services/chat_service.py`. Si quiere entender el esquema de datos de la base de datos, encuentra todo en `src/models/entities.py`.

---

## 4. Componentes del Sistema

### 4.1 Capa de Configuración (src/config/)

#### 4.1.1 Settings: Gestión Centralizada de Configuración

El archivo `settings.py` implementa el patrón de configuración centralizada utilizando Pydantic Settings. Esta clase `Settings` carga automáticamente variables de entorno desde el archivo `.env` y proporciona valores por defecto sensatos para todas las configuraciones del sistema.

La configuración incluye la URL de conexión a la base de datos PostgreSQL, la dirección del servicio Ollama, los nombres de los modelos de embedding y chat, los umbrales de confianza para la toma de decisiones, los parámetros de chunking del texto, y los timeouts para las diferentes operaciones.

La ventaja de centralizar la configuración de esta manera es múltiple. Primero, todos los valores configurables están documentados en un único lugar. Segundo, Pydantic valida automáticamente que los tipos de datos sean correctos. Tercero, los valores pueden sobrescribirse mediante variables de entorno sin modificar código. Cuarto, la función `get_settings()` utiliza caché mediante `@lru_cache`, garantizando que solo se cree una instancia de configuración durante toda la vida de la aplicación.

### 4.2 Capa Core (src/core/)

#### 4.2.1 Constantes y Enumeraciones

El archivo `constants.py` define valores constantes que se utilizan a lo largo de toda la aplicación. La enumeración `DecisionType` establece los tres posibles resultados de una consulta: `ANSWER` cuando el sistema tiene suficiente confianza para responder directamente, `SOFT_DISCLAIMER` cuando hay información parcial pero se requiere precaución, y `DISCLAIMER` cuando no hay evidencia suficiente para dar una respuesta confiable.

Particularmente importante es la tupla `ALLERGY_TRIGGERS`, que contiene treinta y cuatro palabras clave relacionadas con alergias alimentarias. Esta lista incluye términos como "alérgico", "celiaco", "sin tacc", "gluten", "lactosa", "maní", "huevo", "soja", entre otros. El sistema utiliza estas palabras para detectar consultas relacionadas con seguridad alimentaria y activar el modo conservador de respuestas.

#### 4.2.2 Jerarquía de Excepciones

El archivo `exceptions.py` define una jerarquía de excepciones personalizadas que permiten un manejo de errores preciso y significativo. La clase base `AppException` sirve como padre de todas las excepciones específicas del dominio.

`OllamaError` y sus subclases `OllamaConnectionError` y `OllamaTimeoutError` capturan problemas específicos de comunicación con el servicio de inteligencia artificial. `DatabaseError` maneja errores de persistencia. `ValidationError` señala problemas con datos de entrada. `InsufficientEvidenceError` indica cuando no hay suficiente contexto para responder una consulta.

Esta jerarquía permite a los manejadores de errores en la capa API mapear excepciones específicas a códigos HTTP apropiados, proporcionando respuestas significativas al cliente.

### 4.3 Capa de Modelos (src/models/)

#### 4.3.1 Configuración de Base de Datos

El archivo `database.py` centraliza toda la configuración de SQLAlchemy. Define el engine de conexión configurado para PostgreSQL con la extensión psycopg3, crea la factoría de sesiones `SessionLocal`, y proporciona la función generadora `get_db()` que gestiona el ciclo de vida de las sesiones de base de datos.

La función `init_db()` es particularmente importante. Se ejecuta durante el arranque de la aplicación y garantiza que la extensión pgvector esté habilitada, que todas las tablas existan, y que los índices necesarios estén creados. Esta inicialización automática elimina la necesidad de scripts de migración separados para la configuración inicial.

#### 4.3.2 Entidades del Dominio

El archivo `entities.py` define cinco entidades SQLAlchemy que modelan el dominio de la aplicación:

**Dish** representa un plato del menú del restaurante. Contiene el nombre del plato, su categoría (entrada, principal, postre), el precio en centavos para evitar problemas de precisión con decimales, una lista de etiquetas (vegetariano, vegano, sin tacc) almacenada como array PostgreSQL, y un indicador de si el plato está activo en el menú.

**KBChunk** (Knowledge Base Chunk) almacena fragmentos de texto de las fichas técnicas de cada plato. Cada chunk tiene un índice que indica su posición en el documento original, el contenido textual, y metadatos adicionales almacenados como JSON. La relación con Dish es de muchos a uno: cada plato puede tener múltiples chunks que describen sus ingredientes, alérgenos, preparación, etc.

**KBEmbedding** almacena las representaciones vectoriales de cada chunk. El vector de embedding tiene 768 dimensiones, correspondientes al modelo nomic-embed-text de Ollama. La tabla utiliza un índice HNSW (Hierarchical Navigable Small World) de pgvector, optimizado para búsquedas de similitud coseno de alta velocidad.

**ChatTurn** registra cada interacción de conversación. Almacena el texto del usuario, la respuesta del bot, opcionalmente el plato específico sobre el que se preguntó, y la marca temporal.

**RagTrace** proporciona trazabilidad completa del proceso RAG. Para cada consulta, registra qué chunks fueron utilizados, sus scores de similitud, el nivel de confianza calculado, y la decisión tomada. Esta información es invaluable para auditoría, debugging y mejora continua del sistema.

### 4.4 Capa de Esquemas (src/schemas/)

Los esquemas Pydantic definen los contratos de datos para la comunicación entre la API y el mundo exterior.

**ChatIn** especifica el formato de las consultas de chat: la pregunta del usuario (obligatoria, mínimo un carácter), opcionalmente el ID de un plato específico para filtrar la búsqueda, y el número de resultados a recuperar (entre 1 y 12, por defecto 6).

**ChatOut** define la estructura de las respuestas: la respuesta textual generada por el modelo, el tipo de decisión tomada, el nivel de confianza, una lista de fuentes utilizadas con sus scores y previsualizaciones, y el identificador de traza para auditoría.

**DishOut** representa la información de un plato para consumo externo, incluyendo su ID, nombre, categoría, precio y etiquetas.

**HealthResponse** estructura la respuesta del endpoint de salud, indicando si el sistema está operativo, si Ollama es alcanzable, qué modelos están configurados, y las estadísticas de datos (número de platos, chunks y embeddings).

### 4.5 Capa de Repositorios (src/repositories/)

#### 4.5.1 DishRepository

Este repositorio encapsula todas las operaciones relacionadas con platos. El método `get_all_active()` recupera todos los platos disponibles en el menú. `get_by_id()` obtiene un plato específico. `create()` inserta un nuevo plato. `count()` retorna el total de platos activos.

La ventaja de esta abstracción es que el código de servicios no necesita conocer cómo se almacenan los platos. Si en el futuro se decidiera migrar a una base de datos diferente o implementar caché, solo este repositorio necesitaría cambios.

#### 4.5.2 ChunkRepository

Gestiona los fragmentos de conocimiento. `get_unindexed()` identifica chunks que aún no tienen embeddings generados, permitiendo el procesamiento incremental durante la indexación. `create_for_dish()` divide la ficha técnica de un plato en chunks y los persiste.

#### 4.5.3 EmbeddingRepository

Este es quizás el repositorio más crítico del sistema, ya que implementa la búsqueda semántica. El método `search_similar()` recibe un vector de embedding y encuentra los chunks más similares utilizando distancia coseno. La consulta SQL aprovecha el índice HNSW de pgvector para lograr búsquedas sub-lineales incluso con millones de vectores.

La conversión de distancia a score (`score = max(0.0, 1.0 - distance)`) transforma la métrica de distancia en una medida de similitud más intuitiva, donde 1.0 indica coincidencia perfecta y 0.0 indica ninguna relación.

#### 4.5.4 ChatRepository

Persiste las conversaciones y sus trazas. `create_turn()` inicia un nuevo turno de conversación almacenando la pregunta del usuario. `create_trace()` registra la información de trazabilidad RAG después de procesar la consulta. `update_turn_response()` actualiza el turno con la respuesta generada.

Esta separación permite que el historial de conversaciones se registre de manera transaccional, garantizando consistencia incluso si ocurren errores durante el procesamiento.

### 4.6 Capa de Servicios (src/services/)

#### 4.6.1 OllamaService: Puente con la Inteligencia Artificial

Este servicio encapsula toda la comunicación con Ollama. Utiliza httpx como cliente HTTP asíncrono para máximo rendimiento.

El método `generate_embedding()` envía texto al endpoint `/api/embeddings` de Ollama y retorna el vector de 768 dimensiones. Implementa timeout configurable y manejo de errores específico para problemas de conexión.

El método `chat()` envía prompts al modelo de lenguaje a través del endpoint `/api/chat`. Soporta mensajes de sistema y usuario, y tiene un timeout extendido de 300 segundos por defecto para acomodar la generación de texto, que puede ser lenta en hardware modesto.

El método `is_reachable()` proporciona un health check rápido (3 segundos de timeout) para verificar si Ollama está disponible.

#### 4.6.2 TextService: Procesamiento de Texto

Centraliza todas las operaciones de manipulación de texto. El método `normalize_text()` limpia el texto eliminando espacios extra, caracteres de control y normalizando espacios no separables.

El método `chunk_text()` divide textos largos en fragmentos manejables con solapamiento. Utiliza tamaño de 1200 caracteres con 200 caracteres de solapamiento por defecto. Este solapamiento es crucial: garantiza que información que podría estar dividida entre chunks aún mantenga contexto suficiente en cada fragmento para una búsqueda semántica efectiva.

El método `is_allergy_query()` analiza el texto buscando cualquiera de las 34 palabras clave de alérgenos. Cuando detecta una consulta sobre alergias, el sistema activa el modo conservador, siendo más cauteloso en sus respuestas dado el potencial impacto en la salud del usuario.

#### 4.6.3 PromptService: Ingeniería de Prompts

Este servicio gestiona la construcción de prompts para el modelo de lenguaje. El método `build_system_prompt()` genera el prompt de sistema que establece el contexto y las instrucciones base para el modelo. Cuando se detecta una consulta de alergias, añade instrucciones adicionales para ser extremadamente conservador.

El método `build_user_prompt()` construye el prompt de usuario combinando la pregunta original con los fragmentos de evidencia recuperados. Formatea los chunks de manera clara para que el modelo pueda referenciarlos en su respuesta.

El método `build_soft_disclaimer()` genera el texto de advertencia para respuestas con confianza media, indicando que la información debería verificarse con el personal del restaurante.

#### 4.6.4 RetrievalService: Búsqueda Semántica

Orquesta el proceso de recuperación de información. El método `search()` recibe la pregunta del usuario, genera su embedding, busca los chunks más similares, calcula el nivel de confianza basándose en el mejor score obtenido, y determina qué tipo de decisión tomar.

El método privado `_calculate_decision()` implementa la lógica de umbrales: con confianza mayor o igual a 0.78 se responde directamente (`ANSWER`), entre 0.60 y 0.78 se responde con advertencia (`SOFT_DISCLAIMER`), y por debajo de 0.60 se declina responder (`DISCLAIMER`).

Estos umbrales fueron elegidos específicamente pensando en seguridad alimentaria. Es preferible ser demasiado cauteloso y no dar información que dar información incorrecta sobre alérgenos que podría poner en riesgo la salud de una persona.

#### 4.6.5 ChatService: Orquestación del Pipeline RAG

Este es el servicio principal que coordina todo el flujo de procesamiento de una consulta. El método `process_query()` implementa el pipeline completo:

Primero, normaliza la pregunta del usuario y detecta si es una consulta de alergias. Luego crea un nuevo turno de conversación en la base de datos. Después genera el embedding de la pregunta utilizando OllamaService. Realiza la búsqueda semántica a través de RetrievalService.

Con los resultados de la búsqueda, construye los prompts apropiados usando PromptService. Envía los prompts al modelo de lenguaje y obtiene la respuesta. Si la decisión fue `SOFT_DISCLAIMER`, añade la advertencia correspondiente.

Finalmente, registra la traza de la operación para auditoría, actualiza el turno de conversación con la respuesta, y retorna el resultado estructurado al llamador.

#### 4.6.6 SeedService: Inicialización de Datos

Proporciona datos de ejemplo para demostración y pruebas. El método `seed_dishes()` carga diez platos representativos de un menú de restaurante, cada uno con una ficha técnica detallada que incluye descripción, ingredientes, alérgenos, información nutricional y preparación.

Los platos incluyen entradas como burrata con hummus de avellanas, principales como trucha con crema de nabo o risotto de hongos, y postres como brownie con helado. Esta variedad permite probar el sistema con diferentes tipos de consultas sobre ingredientes, preparación y restricciones dietéticas.

### 4.7 Capa API (src/api/)

#### 4.7.1 Sistema de Inyección de Dependencias

El archivo `dependencies.py` implementa el patrón de inyección de dependencias de FastAPI. Define funciones factoría para cada componente del sistema:

`get_settings()` retorna la instancia singleton de configuración. `get_db()` proporciona una sesión de base de datos con gestión automática del ciclo de vida. Las funciones `get_*_repo()` crean instancias de repositorios. Las funciones `get_*_service()` crean instancias de servicios, inyectando las dependencias necesarias.

Esta arquitectura permite que los componentes sean fácilmente intercambiables. Para pruebas, por ejemplo, se pueden proporcionar implementaciones mock de servicios sin modificar el código de los endpoints.

#### 4.7.2 Routers: Endpoints de la API

**health.py** implementa `GET /health`, que verifica el estado del sistema reportando conectividad con Ollama y estadísticas de datos.

**dishes.py** implementa `GET /dishes`, que lista todos los platos activos del menú.

**chat.py** implementa `POST /chat`, el endpoint principal que procesa consultas utilizando el pipeline RAG completo.

**admin.py** implementa `POST /seed` para cargar datos de ejemplo y `POST /index` para generar embeddings de los chunks pendientes.

Cada router es delgado y se limita a validar entrada, delegar a servicios, y formatear respuestas. No contienen lógica de negocio.

---

## 5. Flujo de Datos del Sistema

### 5.1 Flujo de una Consulta de Chat

Cuando un usuario realiza una consulta, el sistema sigue un flujo cuidadosamente orquestado. La petición HTTP llega al endpoint `/chat` con un JSON que contiene la pregunta. FastAPI valida automáticamente la estructura contra el esquema `ChatIn`.

El router extrae la instancia de `ChatService` mediante inyección de dependencias y llama a `process_query()`. El servicio normaliza el texto y verifica si es una consulta sobre alergias.

Se crea un registro en `chat_turn` con la pregunta del usuario. Esto garantiza que incluso si el procesamiento falla posteriormente, la consulta queda registrada.

El servicio de Ollama convierte la pregunta en un vector de 768 dimensiones. Este vector captura la semántica de la pregunta en un espacio matemático donde preguntas similares están cercanas.

El repositorio de embeddings ejecuta una búsqueda de similitud coseno contra todos los chunks indexados. Opcionalmente filtra por un plato específico. Retorna los top-k chunks más relevantes con sus scores.

El servicio de retrieval evalúa la calidad de los resultados. Si el mejor score es 0.85, hay alta confianza. Si es 0.65, confianza media. Si es 0.45, confianza baja o nula.

Basándose en la confianza, se construye un prompt apropiado. Para consultas de alta confianza, el prompt instruye al modelo a responder directamente usando la evidencia. Para confianza media, advierte sobre la incertidumbre. Para confianza baja, el prompt instruye declinar cortésmente.

El modelo de lenguaje genera una respuesta natural basada en el prompt y la evidencia proporcionada. El servicio de chat post-procesa la respuesta, añadiendo disclaimers si es necesario.

Se registra una traza detallada en `rag_trace` con todos los chunks consultados, sus scores, la confianza final y la decisión. Se actualiza `chat_turn` con la respuesta del bot.

Finalmente, se construye el objeto `ChatOut` con la respuesta, metadata y se retorna al usuario como JSON.

### 5.2 Flujo de Indexación

El proceso de indexación convierte fichas técnicas de platos en vectores buscables. Al llamar a `POST /index`, el sistema consulta todos los chunks que no tienen embedding asociado.

Para cada chunk pendiente, se envía el contenido textual a Ollama, que retorna un vector de 768 dimensiones. Este vector se almacena en `kb_embedding` junto con la referencia al chunk origen.

PostgreSQL con pgvector mantiene un índice HNSW sobre estos vectores. Este índice permite búsquedas de similitud en tiempo logarítmico, haciendo el sistema escalable a millones de documentos.

---

## 6. Patrones de Diseño Implementados

### 6.1 Patrón Repository

El patrón Repository abstrae completamente el mecanismo de persistencia. Los servicios trabajan con interfaces de alto nivel como `dish_repo.get_all_active()` sin conocer si los datos provienen de PostgreSQL, MongoDB, o un archivo JSON.

Esta abstracción facilita enormemente las pruebas unitarias. En lugar de necesitar una base de datos real, las pruebas pueden proporcionar implementaciones mock que retornan datos predeterminados.

También permite evolución tecnológica. Si en el futuro se decide implementar caché Redis para platos frecuentes, el cambio se localiza exclusivamente en el repositorio.

### 6.2 Patrón Service Layer

La capa de servicios encapsula toda la lógica de negocio. Los endpoints de la API son completamente agnósticos sobre cómo se procesan las consultas de chat; simplemente delegan a `ChatService`.

Este patrón permite reutilizar la lógica de negocio en diferentes contextos. Si mañana se necesitara un CLI además de la API REST, simplemente crearía una interfaz de línea de comandos que invocara los mismos servicios.

### 6.3 Patrón Dependency Injection

FastAPI facilita la inyección de dependencias mediante el sistema `Depends()`. Cada componente declara explícitamente qué dependencias necesita, y el framework las proporciona automáticamente.

Esta inversión de control tiene múltiples beneficios. Los componentes son más testables porque sus dependencias pueden sustituirse. La configuración está centralizada en `dependencies.py`. Los cambios en cómo se construye una dependencia no afectan a los consumidores.

### 6.4 Patrón Strategy

La lógica de decisión basada en umbrales de confianza implementa implícitamente el patrón Strategy. El sistema tiene tres estrategias de respuesta (`ANSWER`, `SOFT_DISCLAIMER`, `DISCLAIMER`) y selecciona cuál usar basándose en el contexto.

Los umbrales son configurables mediante `Settings`, permitiendo ajustar el comportamiento sin modificar código. Un restaurante muy cauteloso podría subir el umbral de `ANSWER` a 0.90.

### 6.5 Patrón Facade

`ChatService` actúa como una fachada que oculta la complejidad del pipeline RAG. Los clientes de este servicio no necesitan conocer que internamente se coordinan seis servicios diferentes, se realizan llamadas HTTP a Ollama, se ejecutan consultas vectoriales a PostgreSQL, y se registran trazas de auditoría.

---

## 7. Ventajas de la Nueva Arquitectura

### 7.1 Mantenibilidad

El código está organizado de manera que cada archivo tiene una responsabilidad clara y acotada. Cuando se necesita modificar cómo se detectan consultas de alergias, el desarrollador sabe que debe ir a `text_service.py`. Si quiere cambiar los prompts del sistema, examina `prompt_service.py`.

Esta organización reduce drásticamente el tiempo necesario para entender y modificar el código. Un desarrollador nuevo puede comenzar a contribuir productivamente en cuestión de horas, no días.

### 7.2 Testabilidad

La separación de capas permite escribir pruebas unitarias significativas. Se pueden probar las funciones de normalización de texto sin base de datos. Se pueden verificar los umbrales de decisión sin conexión a Ollama. Se pueden validar los esquemas Pydantic sin ninguna infraestructura externa.

El directorio `tests/` incluye fixtures en `conftest.py` que proporcionan mocks para servicios externos, permitiendo pruebas rápidas y deterministas.

### 7.3 Escalabilidad

La arquitectura permite escalar horizontalmente. Múltiples instancias de la API pueden correr detrás de un balanceador de carga, todas conectando a la misma base de datos PostgreSQL.

El patrón Repository facilita implementar estrategias de caché. Los chunks frecuentemente consultados podrían almacenarse en Redis sin cambios en servicios o endpoints.

### 7.4 Extensibilidad

Agregar nuevas funcionalidades es sencillo. Para soportar un nuevo modelo de embeddings, solo se modifica `OllamaService`. Para agregar un nuevo endpoint, se crea un nuevo router sin tocar código existente. Para implementar un nuevo tipo de decisión, se extiende el enum y la lógica de `RetrievalService`.

### 7.5 Seguridad Alimentaria

El sistema prioriza la seguridad sobre la comodidad. Los umbrales conservadores de confianza garantizan que ante la duda, el sistema sugiera verificar con el personal del restaurante en lugar de dar información potencialmente incorrecta sobre alérgenos.

La detección de consultas de alergias activa automáticamente un modo más restrictivo. El registro completo de trazas permite auditoría de todas las respuestas dadas sobre información sensible.

---

## 8. Esquema de Base de Datos

### 8.1 Diagrama de Entidades

```
                          ┌─────────────┐
                          │    dish     │
                          │─────────────│
                          │ id (PK)     │
                          │ name        │
                          │ category    │
                          │ price_cents │
                          │ tags[]      │
                          │ is_active   │
                          │ created_at  │
                          │ updated_at  │
                          └──────┬──────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
            ▼                    ▼                    ▼
    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
    │   kb_chunk    │    │  chat_turn    │    │               │
    │───────────────│    │───────────────│    │               │
    │ id (PK)       │    │ id (PK)       │    │               │
    │ dish_id (FK)  │    │ dish_id (FK)  │    │               │
    │ chunk_index   │    │ user_text     │    │               │
    │ content       │    │ bot_text      │    │               │
    │ meta_data{}   │    │ created_at    │    │               │
    │ created_at    │    └───────┬───────┘    │               │
    └───────┬───────┘            │            │               │
            │                    ▼            │               │
            ▼            ┌───────────────┐    │               │
    ┌───────────────┐    │  rag_trace    │    │               │
    │ kb_embedding  │    │───────────────│    │               │
    │───────────────│    │ id (PK)       │    │               │
    │ chunk_id(PK)  │◄───│ turn_id (FK)  │    │               │
    │ embedding[768]│    │ chunk_ids[]   │    │               │
    │ created_at    │    │ scores[]      │    │               │
    └───────────────┘    │ confidence    │    │               │
                         │ decision      │    │               │
                         │ created_at    │    │               │
                         └───────────────┘    │               │
```

### 8.2 Descripción de Tablas

La tabla `dish` almacena los platos del menú con su información básica. El campo `tags` es un array PostgreSQL que permite múltiples etiquetas por plato. El indicador `is_active` permite deshabilitar platos sin eliminarlos.

La tabla `kb_chunk` fragmenta las fichas técnicas en pedazos manejables. Cada chunk tiene un índice que preserva el orden original, contenido textual normalizado, y metadata JSON flexible para información adicional.

La tabla `kb_embedding` almacena representaciones vectoriales utilizando el tipo `VECTOR(768)` de pgvector. Un índice HNSW con 16 conexiones por nodo y factor de construcción 64 optimiza las búsquedas de similitud coseno.

La tabla `chat_turn` registra cada interacción usuario-sistema. El campo `dish_id` es opcional; cuando está presente, indica que la consulta se refería a un plato específico.

La tabla `rag_trace` proporciona trazabilidad completa. Los arrays `used_chunk_ids` y `scores` registran exactamente qué evidencia se utilizó y con qué relevancia. Los campos `confidence` y `decision` documentan la lógica aplicada.

---

## 9. Configuración y Despliegue

### 9.1 Variables de Entorno

El sistema se configura mediante variables de entorno, con valores por defecto sensatos:

```env
# Conexión a base de datos
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5434/menu_rag

# Servicio de IA
OLLAMA_URL=http://localhost:11434
EMBED_MODEL=nomic-embed-text
CHAT_MODEL=llama3.2:1b

# Umbrales de decisión
CONFIDENCE_ANSWER_THRESHOLD=0.78
CONFIDENCE_SOFT_THRESHOLD=0.60

# Parámetros de chunking
CHUNK_SIZE=1200
CHUNK_OVERLAP=200

# Timeouts (segundos)
OLLAMA_EMBED_TIMEOUT=60
OLLAMA_CHAT_TIMEOUT=300
```

### 9.2 Docker Compose

El archivo `docker-compose.yml` define el servicio de base de datos:

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    container_name: menu_rag_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: menu_rag
    ports:
      - "5434:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

El puerto 5434 se utiliza para evitar conflictos con instalaciones locales de PostgreSQL que típicamente usan 5432 o 5433.

### 9.3 Proceso de Inicialización

Para poner en marcha el sistema:

1. Iniciar PostgreSQL: `docker compose up -d`
2. Crear entorno virtual: `python -m venv .venv`
3. Activar entorno: `.venv\Scripts\Activate.ps1`
4. Instalar dependencias: `pip install -r requirements.txt`
5. Iniciar servidor: `uvicorn app:app --reload --port 8000`

Al arrancar, la aplicación ejecuta `init_db()` que garantiza que la extensión pgvector esté habilitada y las tablas creadas.

---

## 10. Pruebas Automatizadas

### 10.1 Estructura de Pruebas

El directorio `tests/` organiza las pruebas en dos categorías:

Las pruebas unitarias en `tests/unit/` verifican componentes individuales de manera aislada. No requieren base de datos ni servicios externos. Son rápidas (milisegundos) y deterministas.

Las pruebas de integración en `tests/integration/` verifican el sistema completo. Requieren infraestructura real y son más lentas pero prueban interacciones reales.

### 10.2 Fixtures Compartidos

El archivo `conftest.py` define fixtures reutilizables:

```python
@pytest.fixture
def test_settings() -> Settings:
    """Configuración para pruebas con valores predeterminados."""
    return Settings(
        database_url="sqlite:///:memory:",
        ollama_url="http://test:11434"
    )

@pytest.fixture
def mock_ollama_service() -> MagicMock:
    """Mock del servicio Ollama."""
    mock = MagicMock(spec=OllamaService)
    mock.generate_embedding.return_value = [0.1] * 768
    mock.chat.return_value = "Respuesta de prueba"
    return mock
```

### 10.3 Ejemplos de Pruebas Unitarias

Las pruebas de `TextService` verifican normalización y detección de alergias:

```python
def test_normalize_removes_extra_spaces(text_service):
    result = text_service.normalize_text("  hola   mundo  ")
    assert result == "hola mundo"

def test_is_allergy_query_detects_gluten(text_service):
    assert text_service.is_allergy_query("¿tiene gluten?") is True

def test_is_allergy_query_normal_question(text_service):
    assert text_service.is_allergy_query("¿es picante?") is False
```

Las pruebas de lógica de decisión verifican umbrales:

```python
def test_high_confidence_returns_answer(retrieval_service):
    result = retrieval_service._calculate_decision(0.85, has_hits=True)
    assert result == DecisionType.ANSWER

def test_threshold_boundary(retrieval_service):
    result = retrieval_service._calculate_decision(0.78, has_hits=True)
    assert result == DecisionType.ANSWER

    result = retrieval_service._calculate_decision(0.77, has_hits=True)
    assert result == DecisionType.SOFT_DISCLAIMER
```

---

## 11. Guía de Extensión

### 11.1 Agregar Nuevo Endpoint

Para agregar un nuevo endpoint, por ejemplo `GET /dishes/{id}/allergens`:

1. Crear schema de respuesta en `src/schemas/dish.py`:
```python
class AllergenInfo(BaseModel):
    dish_id: int
    allergens: list[str]
    warnings: list[str]
```

2. Agregar método al repositorio si es necesario.

3. Crear nuevo router o extender existente en `src/api/routers/dishes.py`:
```python
@router.get("/{dish_id}/allergens", response_model=AllergenInfo)
def get_dish_allergens(
    dish_id: int,
    dish_repo: DishRepoDep,
    chunk_repo: ChunkRepoDep
):
    # Implementación
```

4. Registrar router si es nuevo en `src/api/routers/__init__.py`.

### 11.2 Soportar Nuevo Modelo de Embeddings

Para cambiar a un modelo de embeddings diferente:

1. Actualizar `EMBED_MODEL` en `.env`.

2. Ajustar dimensionalidad si difiere de 768 en:
   - `src/models/entities.py`: Definición de `kb_embedding.embedding`
   - `src/config/settings.py`: Agregar `embedding_dimensions`

3. Re-indexar todos los chunks ejecutando `POST /index`.

### 11.3 Implementar Caché

Para agregar caché Redis de embeddings frecuentes:

1. Crear `src/services/cache_service.py`:
```python
class CacheService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def get_embedding(self, text_hash: str) -> list[float] | None:
        cached = await self.redis.get(f"emb:{text_hash}")
        return json.loads(cached) if cached else None

    async def set_embedding(self, text_hash: str, embedding: list[float]):
        await self.redis.setex(f"emb:{text_hash}", 3600, json.dumps(embedding))
```

2. Modificar `OllamaService.generate_embedding()` para consultar caché primero.

3. Agregar dependency en `dependencies.py`.

---

## 12. Consideraciones de Seguridad

### 12.1 Seguridad Alimentaria

El sistema implementa múltiples capas de protección para información crítica de alergias:

La detección automática de consultas sobre alergias activa el modo conservador, requiriendo mayor confianza para dar respuestas directas.

Los umbrales de confianza priorizan seguridad sobre comodidad. Ante la duda, el sistema recomienda verificar con personal del restaurante.

La trazabilidad completa permite auditar qué información se proporcionó sobre alérgenos y con qué nivel de confianza.

### 12.2 Seguridad de la Aplicación

Las consultas SQL utilizan parámetros enlazados a través de SQLAlchemy, previniendo inyección SQL.

La validación de entrada mediante Pydantic rechaza datos malformados antes de procesarlos.

Los timeouts en comunicaciones externas previenen ataques de denegación de servicio por recursos colgados.

---

## 13. Conclusiones

La refactorización del proyecto RAG-Restaurante ha transformado un monolito difícil de mantener en una arquitectura modular, testeable y extensible. La separación en capas claras permite a los desarrolladores trabajar en componentes específicos sin afectar el resto del sistema.

Los patrones de diseño implementados—Repository, Service Layer, Dependency Injection, Strategy y Facade—no son meros ejercicios académicos sino soluciones pragmáticas a problemas reales de mantenibilidad y evolución del software.

El énfasis en seguridad alimentaria, con umbrales conservadores y detección automática de consultas sensibles, demuestra cómo las decisiones técnicas pueden alinearse con valores de negocio críticos.

La estructura de pruebas automatizadas proporciona una red de seguridad para futuros cambios, permitiendo refactorizaciones con confianza.

Este documento debe servir como referencia para cualquier desarrollador que trabaje en el proyecto, proporcionando no solo el "qué" de cada componente sino también el "por qué" de las decisiones arquitectónicas tomadas.

---

## Apéndice A: Glosario

**RAG (Retrieval-Augmented Generation)**: Técnica que combina búsqueda de información con generación de lenguaje natural para producir respuestas fundamentadas en evidencia.

**Embedding**: Representación vectorial de texto donde la semántica se codifica en posición espacial.

**pgvector**: Extensión de PostgreSQL para almacenamiento y búsqueda eficiente de vectores.

**HNSW (Hierarchical Navigable Small World)**: Algoritmo de índice para búsqueda aproximada de vecinos más cercanos.

**Chunking**: Proceso de dividir documentos largos en fragmentos manejables con solapamiento.

**Confidence Score**: Métrica que indica cuán relevantes son los resultados de búsqueda para una consulta.

---

## Apéndice B: Referencias

- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/
- pgvector: https://github.com/pgvector/pgvector
- Ollama: https://ollama.ai/
- Pydantic: https://docs.pydantic.dev/
- Patrón Repository: Martin Fowler, Patterns of Enterprise Application Architecture
- Principios SOLID: Robert C. Martin, Clean Architecture
