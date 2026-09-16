# Notas de trabajo — Prueba técnica Creceré AI

Documento de memoria del proyecto: decisiones tomadas, resultados preliminares y qué falta.
No es un entregable; el entregable es `informe/` + este repositorio.

---

## 1. Pipeline de datos (estado: ✅ terminado)

| Paso | Notebook | Salida |
|---|---|---|
| Transcripción + diarización | `Scripts/transcription.ipynb` | `Transcriptions/{humanos,ia}/` |
| Renombrado, limpieza y asignación de roles | `Scripts/renombrar_transcripciones.ipynb` | `Transcriptions procesadas/transcriptions con agente y deudor/` |
| Base analítica determinística + export de turnos | `Scripts/base_analitica_deterministica.ipynb` | `Base analitica/base_analitica.csv`, `Transcriptions_conTurnos/` |
| Análisis de variables etiquetadas con LLM | `Scripts/base_analitica_LLM.ipynb` | `Base analitica/base_llm.csv`, `contrastes_llm.csv` |

**Corpus final: 97 llamadas** (48 humanas + 49 IA). Se excluyeron 3 de las 100 originales por
no contener conversación real (buzón de voz o cuelgue sin respuesta).

Modelos: Whisper `large-v3` + `pyannote/speaker-diarization-3.1` (GPU T4 en Colab).
Roles AGENTE/DEUDOR resueltos con LLM de chat (prompts en `renombrar_transcripciones.ipynb`,
respuestas en `json_LLM/`).

---

## 2. Las tres preguntas

1. **¿Quién cierra más y mejor?** — resultado de la llamada (compromiso con monto y fecha).
2. **¿Por qué?** — qué conductas del agente explican el cierre.
3. **¿Qué debería cambiar?** — la parte accionable.

---

## 3. Hipótesis y resultados preliminares

Todos los números salen de `Base analitica/base_analitica.csv` (n = 48 humanos / 49 IA).
**Son exploratorios: todavía sin tests de significancia.**

Se recortó el set de hipótesis de 7 a **4**. Se descartaron las que dependían solo de detectar
palabras sueltas de empatía, "gates" de permiso o mención de canal de pago: ese método no
verifica el sentido de la frase (un "entiendo" puede o no ir acompañado de una concesión real,
y contarlo sin ese contexto es poco robusto). Quedan las 4 que se apoyan en tiempos, metadatos
o patrones de texto más específicos y fáciles de verificar a mano.

| | Hipótesis | Métrica | Humano | IA |
|---|---|---|---|---|
| **H1** | La IA responde más lento y rompe el ritmo | latencia mediana de respuesta del agente | **0,27 s** | **1,87 s** |
| | | silencio en la llamada | 16 % | 22 % |
| | | *control:* latencia del deudor | 0,11 s | 0,86 s |
| **H2** | La IA sustituye persuasión por presión legal | menciones legales/urgencia por llamada | 1,00 | **3,00** |
| | | llamadas con ≥1 mención | 33 % | **80 %** |
| **H3** | La IA cumple mejor el protocolo de apertura | se identifica | 60 % | **80 %** |
| | | verifica identidad del interlocutor | 27 % | **47 %** |
| **H4** | La llamada de IA es más auditable | diarización colapsada a 1 hablante | 29 % | **0 %** |

### Lectura rápida
- **H1 es el hallazgo más fuerte y más comunicable:** ≈7x de diferencia en latencia. Pendiente
  recalcular sobre diarización limpia antes de publicarlo (ver caveats).
- **H3 salió al revés de lo esperado** y a favor de la IA: cumple el guion de apertura con más
  consistencia que el humano. Es el mejor material para "¿qué hace mejor la IA?".
- **H2 y H4 son directas de comunicar** sin mayor matiz: la IA presiona más y su llamada es
  100 % auditable automáticamente frente al 71 % de las humanas.

---

## 3b. Variables etiquetadas con LLM (V1, V3, V4, V5, V7)

Etiquetado semántico sobre los turnos exportados, con el prompt que está en
`Scripts/base_analitica_LLM.ipynb`. **Cobertura actual: 90/97** (humano 46/48, IA 44/49).
Contrastes con **prueba exacta de Fisher bilateral** (no chi-cuadrado: hay celdas con muy
pocos casos, ej. `compromiso_vago` = 3 en humanos y 0 en IA).

| Contraste | Humano | IA | Dif. | p |
|---|---|---|---|---|
| Cierra compromiso firme | 59 % | **25 %** | −34 pp | 0,0015 ** |
| Llamada sin conclusión | 4 % | **43 %** | +39 pp | <0,0001 *** |
| Cierre operativo claro (cómo/cuándo/dónde pagar) | 59 % | **20 %** | −38 pp | 0,0003 *** |
| Concede ante objeción *(solo llamadas con objeción)* | 62 % | **29 %** | −33 pp | 0,0086 ** |
| Objeción por desconfianza | 11 % | 27 % | +16 pp | 0,0609 ns |
| Tono cordial | 91 % | **45 %** | −46 pp | <0,0001 *** |

**Robustez:** restringiendo a las llamadas de confianza `alta` del LLM (70 % de humanas, 86 %
de IA), el hallazgo central se mantiene y se refuerza: compromiso firme 72 % vs 21 %, p<0,0001.

**Validación del insumo:** cero valores fuera del catálogo de categorías del prompt.

### Lectura
La IA no pierde por lo que dice, sino por **dónde termina la conversación**: casi la mitad de
sus llamadas no llegan a ningún desenlace, y cuando logra un acuerdo no aterriza el mecanismo
de pago. El dato de tono descarta la preocupación inicial de que el LLM etiquetara todo como
"cordial" por defecto: discrimina bien (IA suena neutra en 52 % vs 9 % de humanos).

### Notas de método
- `Concede ante objeción` se calcula **excluyendo** `no_aplica`: meter las llamadas sin objeción
  en el denominador confundiría "no concedió" con "no tuvo nada que conceder".
- Se binariza cada contraste en vez de testear la tabla 2×5 completa: una tabla responde "¿las
  distribuciones difieren?", que no es accionable; binarizar da diferencia en puntos
  porcentuales, directamente comunicable.
- Ojo: **V4 y V5 recuperan, bien hechas, dos de las hipótesis léxicas descartadas** (empatía con
  concesión y canal de pago). Ahora se juzgan por sentido y ambas salieron significativas,
  cuando en su versión léxica eran débiles o ruidosas.

---

### Hipótesis descartadas (referencia, no se usan en el informe)
Quedan documentadas por si conviene retomarlas más adelante, pero no forman parte del análisis
principal porque su método (buscar palabras sin verificar el sentido de la frase) es poco
robusto:
- La IA verbaliza empatía sin traducirla en concesiones (proxy: "entiendo" seguido o no de
  cifra/fecha nueva).
- La IA gasta turnos pidiendo permiso en vez de negociar (proxy: preguntas-compuerta y
  *time-to-offer*).
- El humano cierra la operación (dice cómo pagar) más que la IA (proxy: mención de canal de
  pago).

---

## 4. Caveats que hay que respetar

1. **Latencia sobre diarización limpia.** En 29 % de las llamadas humanas la diarización
   colapsó a un hablante y los cambios de rol los puso el LLM, no el audio. Recalcular H1
   sobre `diarizacion_limpia == 1` antes de publicar el número.
2. **Medianas y tests no paramétricos por defecto:** hay un outlier humano de 1.233 s (20 min).
3. **Los audios están censurados** con un pitido sobre nombres y entidades: ninguna métrica
   puede depender de nombres propios ni de la marca de la empresa.
4. **`se_identifica` / `verifica_identidad`** detectan la *fórmula* de presentación, no la
   identificación real (imposible por la censura). Interpretar como cumplimiento de guion.
5. **`n_presion_legal`** es un patrón léxico: cuenta la aparición de la palabra, no verifica si
   la frase la usa en sentido de amenaza (ej. una negación como "no habrá acciones legales"
   también contaría). Poco probable en este dominio, pero es una limitación real del método.

---

## 5. Pendiente

- [x] **Etiquetado semántico con LLM** — hecho para 90/97 llamadas, analizado en
      `base_analitica_LLM.ipynb`.
- [ ] **Completar el etiquetado:** faltan 2 humanas (`audioh17-440cb585`, `audioh18-50e0f632`)
      y 5 de IA (`audioi16-41269351`, `audioi17-449d76a1`, `audioi18-589afa5a`,
      `audioi19-5a16e288`, `audioi20-631a4d16`).
- [ ] **Auditar a mano 3-4 etiquetas del LLM** contra su transcripción, para confirmar que el
      criterio se sostiene en todo el lote y no solo en los primeros casos.
- [ ] **Notebook de análisis estadístico** para H1–H4 (las determinísticas): Mann-Whitney +
      proporciones, tamaños de efecto, recálculo de H1 sobre el subconjunto de diarización
      limpia.
- [ ] **Modelo explicativo:** regresión logística humano/IA para ver qué variables pesan más
      (el objetivo son los coeficientes, no el accuracy).
- [ ] **Reporte final** (HTML o PDF, pendiente de confirmar con Creceré): máx. 2 páginas.
- [ ] **README del repositorio** con el orden de ejecución de los notebooks.

### Tensión de espacio en el informe
El límite es de 2 páginas muy visuales. El `informe.tex` actual dedica casi todo el espacio a
metodología y calidad de la medición. Al agregar resultados no va a caber: la metodología
detallada debería moverse a un anexo o al README, dejando las 2 páginas para hipótesis,
comparación y hallazgos.

---

## 6. Entrega

- **Deadline:** martes 15 de septiembre de 2026.
- **Correos:** guibor@, nicolas.mendoza@, roberto@, tatiana@ (todos `@crecere.ai`).
- **Asunto:** `PRUEBA TÉCNICA – NOMBRE APELLIDO – CÉDULA`
- **Obligatorio:** reporte final **y** link al repositorio público. Si falta uno, se considera
  incompleta.
