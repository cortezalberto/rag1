# Plan de Optimizacion RAG-Restaurante: De MVP a Produccion

## Introduccion y Vision del Proyecto

Este documento constituye la hoja de ruta tecnica para evolucionar el sistema RAG-Restaurante desde su estado actual como producto minimo viable hacia una solucion robusta lista para operar en entornos de produccion real. El trabajo de auditoria realizado ha identificado que, si bien la arquitectura fundacional es solida y sigue buenas practicas de ingenieria de software, existen brechas criticas que deben cerrarse antes de que el sistema pueda desplegarse en un restaurante real, especialmente considerando las implicaciones de seguridad alimentaria inherentes al dominio.

La transformacion propuesta no implica una reescritura completa del sistema. Por el contrario, aprovecha la inversion ya realizada en la arquitectura en capas, el pipeline RAG funcional y la infraestructura de trazabilidad existente. Lo que se propone es una evolucion incremental y controlada que agregue las capacidades necesarias para operar de manera segura y escalable.

---

## Parte I: Diagnostico del Estado Actual

### Lo Que Funciona Bien

Antes de adentrarnos en las areas de mejora, es importante reconocer los aspectos del sistema actual que estan bien resueltos y que constituyen una base solida sobre la cual construir.

La arquitectura en capas implementada representa una decision de diseno acertada. El sistema actual separa claramente las responsabilidades entre la capa de API (que maneja requests HTTP y validacion), la capa de servicios (que orquesta la logica de negocio), la capa de repositorios (que abstrae el acceso a datos) y la capa de modelos (que define las entidades de dominio). Esta separacion no es meramente estetica: permite que cada componente evolucione de manera independiente, facilita las pruebas unitarias y hace predecible el flujo de datos a traves del sistema. En el contexto de un restaurante, donde los requerimientos tienden a expandirse rapidamente (menus por sucursal, alergenos, disponibilidad, promociones, horarios especiales), esta modularidad sera invaluable.

El pipeline RAG implementado en el ChatService sigue una secuencia logica y completa: normaliza la consulta del usuario, detecta si se trata de una pregunta relacionada con alergias, registra el turno de conversacion, genera el embedding de la consulta, recupera chunks similares, construye los prompts y genera la respuesta. Esta "columna vertebral" del sistema esta bien definida y sera preservada en la version 2.

La decision de mantener trazabilidad explicita mediante las entidades ChatTurn y RagTrace es especialmente valiosa en un dominio con riesgo alimentario. Cada respuesta del sistema queda vinculada a la evidencia que la sustento, los scores de similitud obtenidos y la decision tomada. Esto permite auditar retrospectivamente cualquier respuesta y ajustar umbrales o prompts basandose en datos reales.

Finalmente, la eleccion tecnologica de PostgreSQL con pgvector y indices HNSW es pragmatica y apropiada. Para un restaurante o cadena mediana, esta combinacion ofrece un balance optimo entre simplicidad operativa, consistencia transaccional y rendimiento de busqueda vectorial.

### Las Brechas Criticas

Sin embargo, el analisis tambien revela limitaciones significativas que impiden el despliegue en produccion.

**La ausencia de scope multi-tenant y multi-sucursal** representa el riesgo mas critico. En su estado actual, el sistema no distingue entre diferentes restaurantes ni entre sucursales de una misma cadena. Esto significa que si se desplegara para una cadena con multiples locales, el RAG podria mezclar evidencia de diferentes sucursales al responder una consulta. Las implicaciones son graves: un plato podria ser "sin TACC" en una sucursal pero no en otra debido a diferencias en proveedores o en la cocina. Una respuesta incorrecta sobre alergenos derivada de esta mezcla de evidencia podria tener consecuencias para la salud de los comensales.

**El chunking por caracteres** es suficiente para un prototipo pero riesgoso para precision fina. El sistema actual divide el texto de las fichas tecnicas en fragmentos de 1200 caracteres con un solapamiento de 200, sin considerar la estructura semantica del contenido. En el dominio de restaurantes, la precision depende de micro-hechos: "contiene salsa de soja", "caldo de pollo", "trazas de gluten", "se frie en el mismo aceite". Cuando un chunk mezcla la seccion de ingredientes con la de variantes o advertencias, el modelo de lenguaje puede producir respuestas ambiguas o incorrectas.

**Los umbrales de confianza globales** no distinguen entre tipos de riesgo. Actualmente, el sistema usa los mismos umbrales (0.78 para respuesta directa, 0.60 para respuesta con disclaimer) independientemente de si el usuario pregunta por alergenos potencialmente mortales o por recomendaciones subjetivas de maridaje. Esta uniformidad no refleja la realidad del dominio, donde una consulta sobre celiaquia requiere un nivel de certeza mucho mayor que una sobre si un plato es picante.

**La falta de versionado y vigencia del conocimiento** es problematica en un negocio donde el menu cambia semanalmente. Los ingredientes pueden variar por proveedor, la carta cambia con las temporadas, las recetas se modifican. El sistema actual no tiene forma de saber si la informacion que esta usando esta actualizada o es obsoleta.

**Las respuestas en texto plano** limitan las posibilidades de la interfaz de usuario. El frontend no puede distinguir programaticamente entre diferentes tipos de alertas, no puede mostrar listas estructuradas de alergenos, y no tiene forma de saber si debe recomendar al usuario que verifique con el personal.

---

## Parte II: Arquitectura de la Solucion

### El Modelo de Datos Extendido

La evolucion del modelo de datos es el cimiento sobre el cual se construyen todas las demas mejoras. El objetivo es introducir el concepto de scope (tenant y branch) de manera que cada pieza de informacion en el sistema este inequivocamente asociada a un restaurante y una sucursal especificos.

**Nuevas entidades fundamentales.** Se introducen dos tablas nuevas que no existian en la version 1. La tabla `tenant` representa un restaurante o cadena como entidad de negocio, con su identificador unico, nombre, slug para URLs amigables y un campo JSON para configuraciones especificas. La tabla `branch` representa una sucursal fisica, vinculada a su tenant padre, con informacion adicional como zona horaria y direccion. Esta estructura permite que un mismo sistema sirva a multiples restaurantes, cada uno con multiples sucursales, manteniendo sus datos completamente aislados.

**La evolucion de la tabla dish.** En la version actual, un plato existe de manera global sin asociacion a ningun contexto. En la version 2, cada plato pertenece explicitamente a un tenant y una branch. Esto refleja la realidad de que el mismo plato puede tener variaciones entre sucursales: diferentes precios, ingredientes ligeramente distintos segun el proveedor local, o incluso no estar disponible en algunos locales. Se agrega tambien un campo de codigo interno para integracion con sistemas POS y un timestamp de actualizacion para tracking de cambios.

**La introduccion de kb_document.** Esta nueva tabla representa el concepto de "documento fuente" que no existia en la version 1. Un documento puede ser la ficha de carta completa, notas del chef, una hoja de alergenos oficial, preguntas frecuentes o un glosario de terminos. Cada documento tiene un tipo, un estado (borrador, publicado, archivado), una version y fechas de vigencia. Este modelo permite gestionar el ciclo de vida del conocimiento: un documento nuevo comienza como borrador, se publica cuando esta validado, y se archiva cuando una nueva version lo reemplaza. Solo los documentos publicados y vigentes participan en el retrieval.

**La transformacion de kb_chunk.** Los chunks dejan de ser simples fragmentos de texto para convertirse en unidades semanticas con contexto rico. Cada chunk ahora pertenece a un documento padre, tiene una seccion semantica asociada (ingredientes, alergenos, trazas, tecnica, etc.), un idioma, una estimacion de tokens y metadata estructurada. Esta metadata puede incluir listas explicitas de alergenos detectados, tags dieteticos, version del menu y quien realizo la ultima actualizacion. La vinculacion con un plato especifico es ahora opcional, permitiendo chunks que aplican a multiples platos o al restaurante en general.

**La extension de kb_embedding.** Los embeddings ahora incluyen el scope de tenant y branch, el nombre del modelo que los genero y la dimension del vector. Esto ultimo es importante porque permite cambiar de modelo de embeddings sin necesidad de modificar el esquema de la base de datos, simplemente regenerando los vectores con el nuevo modelo.

**El enriquecimiento de chat_turn y rag_trace.** El registro de conversaciones se extiende para incluir el scope, un identificador de sesion para agrupar turnos relacionados, el rol del actor (cliente, mozo, cocina), la version normalizada de la consulta, la intencion clasificada y el nivel de riesgo determinado. La traza RAG ahora almacena el identificador de la politica aplicada, el numero de candidatos recuperados, la lista completa de candidatos con sus scores originales y finales, y la respuesta estructurada completa en formato JSON.

### El Sistema de Tipos Enriquecido

Para soportar la nueva semantica del sistema, se introducen varios tipos enumerados a nivel de base de datos.

Los estados de documento (`kb_doc_status`) definen el ciclo de vida: DRAFT para documentos en preparacion, PUBLISHED para documentos activos que participan en retrieval, y ARCHIVED para versiones historicas que se conservan pero no se usan.

Los tipos de documento (`kb_doc_type`) categorizan las fuentes de conocimiento: MENU_CARD para fichas de carta, CHEF_NOTES para anotaciones del chef, ALLERGEN_SHEET para hojas oficiales de alergenos, FAQ para preguntas frecuentes, y GLOSSARY para definiciones de terminos.

Las secciones de chunk (`kb_section`) definen la estructura semantica: TITLE, DESCRIPTION, INGREDIENTS, ALLERGENS, TRACES, TECHNIQUE, SUBSTITUTIONS, PAIRING, FAQ y GLOSSARY. Esta clasificacion es fundamental para el re-ranking basado en intencion.

Las intenciones de consulta (`rag_intent`) clasifican que tipo de informacion busca el usuario: ALLERGENS para consultas sobre alergias, INGREDIENTS para preguntas sobre composicion, DIETARY para restricciones dieteticas como veganismo, RECOMMENDATION para sugerencias subjetivas, GLOSSARY para definiciones, GENERAL para consultas genericas, AVAILABILITY para disponibilidad (que se redirige al core transaccional), y UNKNOWN para consultas no clasificables.

Las decisiones RAG (`rag_decision`) extienden las tres originales agregando ASK_CLARIFY para situaciones donde el sistema necesita mas informacion del usuario antes de responder.

Los niveles de riesgo (`rag_risk`) categorizan la criticidad: LOW para consultas sin implicaciones de salud, MEDIUM para consultas con implicaciones moderadas, HIGH para restricciones dieteticas importantes, y CRITICAL para alergenos que pueden causar reacciones severas.

---

## Parte III: Transformacion del Pipeline RAG

### De Chunking por Caracteres a Chunking Semantico

El cambio en la estrategia de chunking es una de las transformaciones mas impactantes en terminos de calidad de respuestas.

**El problema con el enfoque actual.** El TextService actual implementa un algoritmo de ventana deslizante que toma el texto completo de una ficha y lo divide en fragmentos de 1200 caracteres, avanzando 1000 caracteres entre fragmentos (dejando 200 de solapamiento). Este enfoque tiene la virtud de la simplicidad, pero ignora completamente la estructura del contenido. Una ficha tecnica tipica tiene secciones claramente diferenciadas: primero una descripcion del plato, luego la lista de ingredientes, despues los alergenos, quiza notas sobre tecnica de preparacion. Cuando el chunking por caracteres corta en medio de una seccion o, peor aun, combina partes de dos secciones diferentes en un mismo chunk, el embedding resultante es una mezcla confusa que no representa bien ninguno de los conceptos originales.

**La solucion semantica.** El nuevo SemanticChunker parsea el texto buscando encabezados de seccion (INGREDIENTES:, ALERGENOS:, etc.) y genera un chunk separado para cada seccion encontrada. Cada chunk queda etiquetado con su tipo de seccion, lo que permite al sistema de retrieval saber exactamente que tipo de informacion contiene. Si un usuario pregunta por alergenos, el sistema puede priorizar chunks de tipo ALLERGENS y TRACES sobre chunks de tipo DESCRIPTION, incluso si estos ultimos tienen un score de similitud vectorial ligeramente mayor.

**El formato de fichas requerido.** Para que el chunking semantico funcione correctamente, las fichas tecnicas deben seguir una estructura con encabezados reconocibles. Esto puede requerir reformatear las fichas existentes, pero el esfuerzo se justifica por la mejora en precision. Un ejemplo de ficha bien estructurada seria:

```
DESCRIPCION:
Corte premium de carne vacuna argentina, madurado 21 dias...

INGREDIENTES:
Carne vacuna (bife de chorizo), sal marina, pimienta negra...

ALERGENOS:
Sin alergenos declarados en los ingredientes principales.

TRAZAS:
Puede contener trazas de mostaza (salsa opcional).

TECNICA:
Coccion a la parrilla con carbon...
```

**La metadata enriquecida.** Cada chunk semantico puede llevar metadata estructurada que facilita el procesamiento posterior. Para un chunk de tipo ALLERGENS, la metadata podria incluir una lista explicita de alergenos detectados (`allergens_explicit`), una lista de posibles contaminaciones cruzadas (`contains_may_contain`), y tags dieteticos relevantes. Esta informacion, extraida durante la ingesta, permite construir respuestas estructuradas sin necesidad de que el LLM la infiera del texto.

### El Sistema de Politicas de Riesgo

La introduccion de politicas diferenciadas por tipo de consulta es fundamental para un sistema de informacion alimentaria responsable.

**La limitacion del enfoque actual.** Con umbrales globales de 0.78 y 0.60, el sistema trata de manera identica una consulta sobre alergenos potencialmente mortales y una pregunta sobre si un plato es picante. Esta uniformidad no refleja la realidad del dominio. Un falso positivo sobre picante es una molestia menor; un falso positivo sobre ausencia de mani puede ser fatal para alguien con alergia severa.

**El concepto de politica.** Una politica RAG define, para cada tipo de intencion, el umbral de confianza requerido, las secciones de chunk preferidas para re-ranking, y el comportamiento ante falta de evidencia. El sistema V2 implementa esto mediante una clase RagPolicy que encapsula estos parametros.

Para consultas de tipo ALLERGENS, la politica especifica un umbral de 0.85 (mas alto que el 0.78 general), prioriza chunks de secciones ALLERGENS, TRACES e INGREDIENTS, y ante cualquier incertidumbre fuerza una respuesta de tipo VERIFY_WITH_STAFF. El nivel de riesgo asociado es CRITICAL.

Para consultas de tipo RECOMMENDATION, la politica es mas permisiva: umbral de 0.60, secciones preferidas DESCRIPTION, PAIRING y TECHNIQUE, y comportamiento conversacional ante incertidumbre. El nivel de riesgo es LOW.

**La clasificacion de intencion.** Antes de aplicar la politica, el sistema debe determinar que tipo de consulta esta procesando. El IntentClassifier analiza la consulta normalizada buscando patrones indicativos. La presencia de terminos como "alerg", "celiac", "sin tacc", "gluten", "mani" indica intencion ALLERGENS. Terminos como "vegano", "vegetariano", "keto" indican DIETARY. Palabras como "hay", "queda", "disponible" indican AVAILABILITY, que se redirige fuera del RAG hacia el sistema transaccional.

Esta clasificacion puede implementarse inicialmente con reglas heuristicas simples y evolucionar hacia un clasificador basado en LLM si los datos de uso revelan patrones mas complejos.

### El Retrieval Mejorado con Filtros y Re-Ranking

El proceso de recuperacion de chunks se transforma para incorporar el scope obligatorio, la validacion de vigencia y un paso de re-ranking basado en reglas.

**El filtrado por scope y vigencia.** Toda consulta de retrieval debe incluir ahora tenant_id y branch_id como parametros obligatorios. La query SQL se construye para filtrar unicamente chunks que pertenezcan al scope correcto, cuyo documento padre tenga estado PUBLISHED, y cuyas fechas de vigencia incluyan el momento actual. Esto garantiza que nunca se mezcle informacion de diferentes sucursales y que nunca se use informacion obsoleta.

**El re-ranking por reglas.** Despues de obtener los top-k candidatos por similitud vectorial, el sistema aplica un paso de re-ranking que ajusta los scores basandose en reglas de negocio. Si la intencion es ALLERGENS y un chunk pertenece a la seccion ALLERGENS o TRACES, recibe un bonus de score. Si un chunk tiene metadata que declara explicitamente los alergenos presentes, recibe un bonus adicional. El score final se calcula como una combinacion ponderada del score base de similitud (70%) y los bonuses por reglas (30%).

Este enfoque hibrido combina la potencia de la busqueda semantica con el conocimiento de dominio codificado en reglas. El resultado es un ranking que refleja mejor la relevancia real para la consulta del usuario.

---

## Parte IV: Respuestas Estructuradas para UX Segura

### El Problema de las Respuestas en Texto Plano

En la version actual, el endpoint de chat devuelve una respuesta que incluye el texto de la respuesta, el tipo de decision, el score de confianza, las fuentes usadas y el ID de traza. Esta estructura es funcional pero insuficiente para construir una experiencia de usuario verdaderamente segura.

El frontend no tiene forma de saber programaticamente si debe mostrar una alerta de seguridad alimentaria. No puede distinguir entre diferentes tipos de incertidumbre. No puede presentar de manera estructurada los alergenos confirmados versus los posibles. Y no tiene orientacion sobre que accion deberia tomar el usuario.

### El AnswerEnvelope como Contrato de Respuesta

La version 2 introduce un contrato de respuesta rico llamado AnswerEnvelope que proporciona toda la informacion necesaria para que el frontend construya una experiencia de usuario apropiada al contexto.

**La estructura de la respuesta.** El envelope incluye la decision tomada (ANSWER, SOFT_DISCLAIMER, DISCLAIMER, ASK_CLARIFY), la intencion clasificada, el nivel de riesgo determinado, una referencia opcional al plato identificado con su confianza, el texto de la respuesta generada, un bloque estructurado de alergenos (con listas separadas para explicitos, posibles y desconocidos), una lista de incertidumbres identificadas, una accion recomendada (SAFE_TO_ORDER, VERIFY_WITH_STAFF, ASK_FOR_DISH, NONE), las fuentes usadas con sus scores, y la informacion de la politica aplicada.

**Como el frontend usa esta informacion.** Cuando el envelope indica `action: VERIFY_WITH_STAFF`, el frontend muestra una alerta prominente recomendando verificacion con el personal. Cuando el bloque de alergenos tiene items en `explicit`, estos se muestran en una lista destacada. Cuando hay items en `uncertainties`, se presentan como advertencias. Cuando la decision es ASK_CLARIFY, el frontend muestra las opciones de platos candidatos para que el usuario especifique.

Esta estructura permite al frontend tomar decisiones de presentacion basadas en datos estructurados en lugar de intentar parsear texto libre, lo que resulta en una experiencia de usuario mas consistente y segura.

---

## Parte V: Gobernanza del Conocimiento

### El Ciclo de Vida de los Documentos

En un restaurante real, el conocimiento no es estatico. Los menus cambian con las temporadas, los ingredientes varian segun el proveedor disponible, las recetas se ajustan, los precios se actualizan. El sistema debe reflejar esta realidad dinamica.

**El modelo de estados.** Un documento comienza su vida en estado DRAFT cuando se crea. En este estado, puede editarse libremente pero no participa en el retrieval. Cuando el contenido esta validado, se publica cambiando su estado a PUBLISHED. Solo los documentos publicados son visibles para el pipeline RAG. Cuando una nueva version del documento esta lista, la anterior se cambia a ARCHIVED y la nueva se publica. Los documentos archivados se conservan para auditoria historica pero no participan en retrieval.

**La vigencia temporal.** Ademas del estado, cada documento tiene fechas de vigencia (effective_from, effective_to). Un documento puede estar publicado pero fuera de su periodo de vigencia, en cuyo caso tampoco participa en retrieval. Esto permite programar cambios de menu con anticipacion: se puede crear y publicar el menu de verano con fecha de vigencia futura, y automaticamente entrara en efecto cuando llegue esa fecha.

**El versionado.** Cada documento tiene un numero de version que se incrementa con cada actualizacion significativa. Esto permite rastrear la evolucion del contenido y, en caso de problemas, identificar exactamente que version de la informacion estaba activa cuando se produjo una respuesta especifica.

### Los Endpoints de Administracion

La gestion del ciclo de vida se realiza a traves de endpoints administrativos dedicados.

El endpoint de creacion permite subir un nuevo documento especificando su tipo, titulo, fuente y fechas de vigencia. El documento se crea en estado DRAFT.

El endpoint de publicacion cambia el estado de un documento de DRAFT a PUBLISHED, haciendolo disponible para retrieval.

El endpoint de ingesta procesa un documento publicado: extrae el texto (posiblemente desde un PDF o archivo estructurado), aplica el chunking semantico, genera los embeddings para cada chunk, y almacena todo en la base de datos.

El endpoint de salud permite monitorear el estado de la base de conocimiento: cuantos documentos hay en cada estado, cuando fue la ultima ingesta, cuantos chunks y embeddings existen.

---

## Parte VI: Arquitectura Multi-Tenant

### El Contexto Obligatorio

En la version 2, toda interaccion con el sistema requiere especificar el contexto de tenant y branch. Esto se logra mediante cambios en los contratos de API y en la logica de acceso a datos.

**El request enriquecido.** Cada consulta al endpoint RAG debe incluir tenant_slug (identificador del restaurante), branch_slug (identificador de la sucursal), session_id (para agrupar turnos de una misma conversacion), el texto de la consulta, y opcionalmente el rol del actor. El frontend tipicamente obtiene tenant_slug y branch_slug del contexto de la aplicacion (por ejemplo, de la URL del menu QR escaneado).

**La resolucion de scope.** El backend resuelve los slugs a IDs internos consultando las tablas tenant y branch. Si alguno no existe, la request falla temprano con un error claro. Los IDs resueltos se propagan a todas las operaciones subsiguientes.

**El filtrado universal.** Toda query a la base de datos que involucre datos de negocio (platos, chunks, embeddings, conversaciones) debe incluir clausulas WHERE que filtren por tenant_id y branch_id. Esto no es opcional ni situacional: es una regla de hierro que garantiza el aislamiento de datos entre diferentes clientes del sistema.

### Los Riesgos de la Mezcla de Evidencia

Para entender por que el aislamiento multi-tenant es critico, consideremos un escenario concreto.

Una cadena de restaurantes tiene dos sucursales: Palermo y Belgrano. En la sucursal Palermo, el proveedor de pan es uno que garantiza "sin TACC". En la sucursal Belgrano, por razones de disponibilidad, usan un proveedor diferente cuyo pan contiene gluten.

Si el sistema no aislara por sucursal, un cliente celiaco en Belgrano podria preguntar si las milanesas son aptas, el RAG podria recuperar chunks de la sucursal Palermo que dicen "pan sin TACC", y responder afirmativamente. El resultado podria ser una reaccion alergica severa.

El scope obligatorio elimina esta posibilidad: las queries de clientes en Belgrano solo ven evidencia de Belgrano.

---

## Parte VII: La Identificacion Previa de Plato

### El Problema de las Consultas Ambiguas

Un patron comun de consulta es preguntar sobre un plato sin nombrarlo completamente o refiriendose a el de manera informal. "Tiene gluten?" sin especificar que plato. "El bife tiene lactosa?" cuando hay multiples variantes de bife en el menu.

En estos casos, el RAG actual busca en toda la base de conocimiento, recupera chunks de multiples platos, y el LLM debe inferir a cual se refiere el usuario. Esto introduce ambiguedad y reduce la precision de las respuestas.

### El Flujo de Dish Resolve

La version 2 introduce un paso previo de identificacion de plato que mejora significativamente la precision.

**La extraccion de candidatos.** Cuando llega una consulta, el sistema primero intenta identificar si menciona un plato. Busca en la tabla de dishes por coincidencia parcial de nombre (ILIKE) y opcionalmente por similitud semantica del embedding del nombre.

**La logica de decision.** Si se encuentra un unico candidato con alta confianza (por ejemplo, >0.80), el retrieval posterior se filtra por el dish_id de ese plato, garantizando que solo se recuperen chunks relevantes.

Si se encuentran multiples candidatos con confianzas similares, el sistema devuelve una respuesta de tipo ASK_CLARIFY presentando las opciones: "Te referis al Bife de Chorizo o al Bife de Lomo?"

Si no se encuentra ningun candidato, el retrieval procede sin filtro de plato pero el sistema puede agregar una incertidumbre indicando que no pudo identificar el plato especifico.

**El beneficio en precision.** Cuando el retrieval se filtra por dish_id, los chunks recuperados son todos del mismo plato, eliminando la ambiguedad. Los scores de similitud son mas significativos porque comparan contra un contexto homogeneo. El resultado es una respuesta mas precisa y confiable.

---

## Parte VIII: La Separacion entre Core y RAG

### El Principio Arquitectonico

Un restaurante real opera con dos tipos de informacion fundamentalmente diferentes.

La informacion estatica incluye descripciones de platos, ingredientes, alergenos, tecnicas de preparacion, historias de origen. Esta informacion cambia infrecuentemente y de manera planificada. Es el dominio natural del RAG.

La informacion dinamica incluye disponibilidad actual, tiempos estimados de preparacion, promociones activas, precios del dia. Esta informacion cambia constantemente basada en el estado operativo del restaurante. Es el dominio del sistema transaccional (POS, gestion de inventario, etc.).

**El riesgo de mezclar dominios.** Si el RAG intentara responder preguntas de disponibilidad basandose en su base de conocimiento, las respuestas serian incorrectas frecuentemente. "Si, tenemos el salmon" cuando en realidad se agoto hace una hora. Estas respuestas incorrectas frustran a los clientes y generan problemas operativos.

### La Implementacion del Desvio

Cuando el clasificador de intencion detecta una consulta de tipo AVAILABILITY, el sistema no ejecuta el pipeline RAG completo. En su lugar, devuelve inmediatamente una respuesta predefinida que redirige al usuario hacia el canal apropiado: "La disponibilidad se confirma con el personal o a traves del sistema de pedidos."

Esta separacion clara evita que el RAG de respuestas incorrectas sobre informacion que no puede conocer, y educa al usuario sobre donde obtener ese tipo de informacion.

---

## Parte IX: Plan de Implementacion

### Filosofia de Migracion

La transformacion de V1 a V2 debe realizarse de manera incremental y reversible. Cada fase agrega capacidades nuevas sin romper la funcionalidad existente. Se mantiene compatibilidad hacia atras hasta que todos los consumidores esten migrados.

### Fase 1: Fundamentos Multi-Tenant

La primera fase establece la infraestructura de scope sin modificar el comportamiento del sistema.

Se crean las tablas tenant y branch. Se agregan las columnas tenant_id y branch_id a todas las tablas existentes, inicialmente como nullable. Se crea un tenant y branch "default" y se migran todos los datos existentes a este scope. Se hacen las columnas NOT NULL. Se actualizan los repositorios para aceptar y filtrar por scope, pero el API externo sigue funcionando sin cambios usando el scope default implicitamente.

Al final de esta fase, la base de datos soporta multi-tenant pero el sistema se comporta exactamente igual que antes para los usuarios existentes.

### Fase 2: Chunking Semantico

La segunda fase mejora la calidad del retrieval sin cambiar la interfaz externa.

Se crea la tabla kb_document. Se agrega la columna section a kb_chunk. Se implementa el SemanticChunker. Se crean los endpoints de administracion de documentos. Se migran los chunks existentes asignandoles seccion DESCRIPTION por defecto. Se re-procesan las fichas originales con el nuevo chunker. Se regeneran los embeddings.

Al final de esta fase, el retrieval es mas preciso pero el API externo no cambia.

### Fase 3: Politicas de Riesgo

La tercera fase introduce comportamiento diferenciado por tipo de consulta.

Se implementa RagPolicy con los umbrales por intencion. Se implementa IntentClassifier. Se modifica RetrievalService para aplicar la politica segun intencion. Se implementa el re-ranking por secciones preferidas. Se agregan intent y risk_level a chat_turn.

Al final de esta fase, las consultas sobre alergenos reciben tratamiento mas conservador que las consultas generales.

### Fase 4: Respuestas Estructuradas

La cuarta fase transforma el contrato de respuesta.

Se define el schema AnswerEnvelope. Se modifica ChatService para construir el envelope. Se actualiza PromptService para guiar al LLM hacia respuestas que faciliten la extraccion de datos estructurados. Se crea un nuevo endpoint V2 que devuelve AnswerEnvelope. Se mantiene el endpoint V1 original por compatibilidad.

Al final de esta fase, los consumidores pueden elegir entre el formato de respuesta V1 o V2.

### Fase 5: Dish Resolve

La quinta fase agrega la identificacion previa de plato.

Se implementa el endpoint dish/resolve. Se integra la logica de resolucion en el flujo principal de query. Se implementa la respuesta ASK_CLARIFY cuando hay ambiguedad. Se implementa el fallback cuando un plato no tiene chunks asociados.

Al final de esta fase, las consultas sobre platos especificos son significativamente mas precisas.

### Fase 6: Observabilidad y Lanzamiento

La fase final prepara el sistema para operacion real.

Se implementa un dashboard de metricas mostrando tasas de decision por tipo, latencias, gaps de cobertura. Se configuran alertas para anomalias. Se actualiza la documentacion de API. Se actualizan y expanden los tests. Se realizan pruebas de carga. Se preparan runbooks operativos.

Al final de esta fase, el sistema esta listo para produccion.

---

## Parte X: Verificacion y Metricas

### Criterios de Exito

El exito de la migracion se medira contra metricas concretas.

La precision en consultas de alergenos debe superar el 90%, medida como el porcentaje de respuestas que un revisor humano califica como correctas y completas. La version actual se estima en aproximadamente 70%.

La tasa de respuestas DISCLAIMER debe reducirse por debajo del 15%, indicando que el sistema encuentra evidencia relevante para la mayoria de las consultas. La version actual se estima en aproximadamente 25%.

La latencia del percentil 95 debe mantenerse por debajo de 2 segundos, asegurando una experiencia de usuario fluida. Esto puede requerir optimizacion de queries y posiblemente cache de embeddings para consultas frecuentes.

La trazabilidad debe ser completa: cada respuesta debe poder auditarse retrospectivamente hasta la evidencia que la sustento, la politica que se aplico, y la decision que se tomo.

### Gestion de Riesgos

**Riesgo de regresion durante migracion.** Mitigacion: migracion en fases pequenas, cada una con sus propios tests de regresion, capacidad de rollback rapido.

**Riesgo de chunking semantico mal parseado.** Mitigacion: validacion de formato de fichas antes de ingesta, fallback a seccion DESCRIPTION para contenido no estructurado, revision manual de resultados de chunking.

**Riesgo de clasificacion de intencion incorrecta.** Mitigacion: umbral conservador para categoria UNKNOWN que se trata con la politica mas restrictiva, logging detallado para analisis posterior y mejora del clasificador.

**Riesgo de degradacion de performance.** Mitigacion: indices optimizados para los nuevos patrones de query, cache de embeddings para consultas frecuentes, monitoreo continuo de latencias.

**Riesgo de indisponibilidad de Ollama.** Mitigacion: healthcheck proactivo, fallback a respuesta DISCLAIMER fija con recomendacion de verificar con personal, alertas para equipo de operaciones.

---

## Conclusion

La evolucion de RAG-Restaurante de V1 a V2 representa una maduracion significativa del sistema, transformandolo de un prototipo funcional en una solucion lista para produccion. Los cambios propuestos no son cosmeticos: abordan riesgos reales de seguridad alimentaria, establecen fundamentos para escalabilidad multi-tenant, y proporcionan la infraestructura necesaria para operacion y mejora continua.

El enfoque incremental de la migracion minimiza riesgos y permite validar cada mejora antes de proceder a la siguiente. Al final del proceso, el sistema no solo sera mas seguro y preciso, sino que estara instrumentado para evolucionar basandose en datos de uso real.

La inversion en esta transformacion se justifica por el dominio de aplicacion: en un sistema de informacion alimentaria, la diferencia entre "funciona" y "funciona de manera confiable y auditable" puede ser literalmente la diferencia entre la salud y la enfermedad de los usuarios finales.

---

*Documento de arquitectura y planificacion*
*Version 2.0*
*Fecha: Enero 2026*
