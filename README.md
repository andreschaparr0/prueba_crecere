# Prueba técnica — Creceré AI

**Gestión de cobranza: agentes humanos vs. agentes de IA.** Este repositorio contiene el
análisis completo: desde el audio crudo hasta el reporte final, pasando por transcripción,
diarización, construcción de variables y contraste estadístico entre los dos grupos.

La pregunta que persigue todo el pipeline es simple de enunciar y difícil de responder bien:
*¿existen diferencias reales entre cómo gestiona un humano y cómo gestiona una IA, y en qué
consisten?*

## Entregables

- **Reporte final:** `Entregable/reporte.html`
- **Este repositorio:** todo el código de construcción de datos, análisis estadístico y
  generación del reporte.

## Cómo está organizado

- `Audios/` — grabaciones originales (humanas e IA), censuradas con un pitido sobre nombres
  y entidades.
- `Transcriptions/` — transcripción y diarización cruda, un JSON por llamada.
- `Transcriptions procesadas/` — llamadas renombradas a IDs trazables, con roles AGENTE/DEUDOR
  resueltos, exportadas en turnos de texto plano, y las respuestas del etiquetado semántico
  con LLM.
- `Base analitica/` — los CSV finales que alimentan el análisis y el reporte.
- `Scripts/` — los notebooks, en el orden en que se ejecutan (ver más abajo).
- `informe/` — fuente LaTeX del informe.
- `Entregable/` — el reporte final en HTML.
- `NOTAS.md` — la memoria de trabajo: decisiones tomadas, resultados numéricos y pendientes.

## El pipeline, paso a paso

**1. `Scripts/transcription.ipynb`** — Whisper `large-v3` transcribe cada audio y
`pyannote.audio` separa a los hablantes (corrido sobre GPU, en Google Colab). Entra `Audios/`,
sale `Transcriptions/`.

**2. `Scripts/renombrar_transcripciones.ipynb`** — limpieza y trazabilidad: IDs cortos,
descarte de llamadas sin conversación real (buzones de voz), y la pregunta de fondo *¿cuál
etiqueta es el agente y cuál el deudor?* — la diarización no lo sabe, así que se resolvió con
un LLM de chat leyendo cada apertura de llamada. Los prompts usados quedan documentados dentro
del propio notebook.

**3. `Scripts/base_analitica_deterministica.ipynb`** — construye la primera capa de variables,
las que se pueden calcular sin interpretar el sentido de una frase: ritmo conversacional,
presión y urgencia en el discurso, cumplimiento del protocolo de apertura, calidad de la
diarización. Solo usa librería estándar de Python — corre en cualquier máquina sin instalar
nada. Cierra exportando cada llamada como un guion de texto plano, que es el insumo del
siguiente paso.

**4. Etiquetado semántico con LLM** — hay preguntas que ningún patrón de texto puede responder
bien: ¿cerró la negociación? ¿qué objeción puso el deudor? ¿el agente cedió algo concreto?
Los guiones de texto del paso 3 se llevan a un LLM de chat con el prompt documentado en
`Scripts/base_analitica_LLM.ipynb`, y las respuestas se guardan como JSON.

**5. `Scripts/base_analitica_LLM.ipynb`** — toma esas respuestas, mide cuánto difieren los dos
grupos en cada variable y contrasta esa diferencia con una prueba estadística, para separar
una diferencia real de una casualidad de muestreo.

**6. `informe/informe.tex` y `Entregable/reporte.html`** — el cierre: los hallazgos, ya
depurados de todo el trabajo anterior, en el formato que se puede mostrar a alguien que nunca
vio el código.

## Reproducibilidad

Los notebooks de los pasos 3 y 5 son deterministas y no dependen de nada externo: se pueden
volver a correr en cualquier momento sobre los datos ya procesados y dan exactamente el mismo
resultado. Los pasos 1, 2 y 4 dependen de modelos externos (Whisper, pyannote, un LLM de chat)
y de una revisión humana en el camino — no están pensados para reproducirse en automático,
sus resultados ya quedaron guardados en el repositorio tal como se usaron.

## Método, en breve

- Se excluyeron las llamadas sin conversación real (buzón de voz o cuelgue sin respuesta):
  el análisis compara gestión efectiva, no intentos de contacto fallidos.
- Las hipótesis sobre ritmo, presión, protocolo y auditabilidad se contrastan con Mann-Whitney
  U (variables continuas) y la prueba exacta de Fisher (variables binarias).
- Las variables de resultado, objeción, concesión, cierre y tono —etiquetadas con LLM— se
  contrastan también con la prueba exacta de Fisher.
- El razonamiento detrás de cada decisión, los números completos y lo que queda pendiente
  están en `NOTAS.md`.

## Una nota sobre los datos

Los audios llegan censurados con un pitido sobre nombres propios y el nombre de la entidad que
gestiona la cobranza. Ninguna variable de este análisis depende de esa información censurada.
