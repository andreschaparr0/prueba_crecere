# Notas de trabajo — Prueba técnica Creceré AI

Documento de memoria del proyecto: decisiones tomadas, resultados preliminares y qué falta.
No es un entregable; el entregable es `informe/` + este repositorio.

---

## 1. Pipeline de datos (estado: ✅ terminado)

| Paso | Notebook | Salida |
|---|---|---|
| Transcripción + diarización | `Scripts/transcription.ipynb` | `Transcriptions/{humanos,ia}/` |
| Renombrado, limpieza y asignación de roles | `Scripts/renombrar_transcripciones.ipynb` | `Transcriptions procesadas/transcriptions con agente y deudor/` |
| Base analítica (una fila por llamada) | `Scripts/base_analitica.ipynb` | `Base analitica/base_analitica.csv` |

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

| | Hipótesis | Métrica | Humano | IA |
|---|---|---|---|---|
| **H1** | La IA responde más lento y rompe el ritmo | latencia mediana de respuesta del agente | **0,27 s** | **1,87 s** |
| | | silencio en la llamada | 16 % | 22 % |
| | | *control:* latencia del deudor | 0,11 s | 0,86 s |
| **H2** | La IA sustituye persuasión por presión legal | menciones legales/urgencia por llamada | 1,00 | **3,00** |
| | | llamadas con ≥1 mención | 33 % | **80 %** |
| **H3** | La IA verbaliza empatía sin traducirla en concesiones | "entiendo/comprendo" por llamada | 0,94 | **2,47** |
| | | de esas, seguidas de cifra o fecha nueva | 0,56 | 1,27 |
| **H4** | La IA gasta turnos pidiendo permiso | preguntas-compuerta por llamada | 0,02 | **1,08** |
| | | *time-to-offer* (1ª cifra concreta) | **22,4 s** | 40,2 s |
| **H5** | El humano cierra la operación; la IA solo el acuerdo | menciona canal de pago | **71 %** | 31 % |
| | | menciona alguna cifra concreta | **77 %** | 63 % |
| **H6** | La IA cumple mejor el protocolo de apertura | se identifica | 60 % | **80 %** |
| | | verifica identidad del interlocutor | 27 % | **47 %** |
| **H7** | La llamada de IA es más auditable | diarización colapsada a 1 hablante | 29 % | **0 %** |
| — | Huella de habla espontánea | muletillas por 100 palabras | **2,66** | 0,18 |

### Lectura rápida
- **H1 es el hallazgo más fuerte y más comunicable:** ≈7x de diferencia en latencia.
- **H6 salió al revés de lo esperado** y a favor de la IA: cumple el guion de apertura con más
  consistencia que el humano. Es el mejor material para "¿qué hace mejor la IA?".
- **H5 es el hallazgo más accionable:** la IA acuerda pero no explica cómo pagar.
- **H4 tiene evidencia cualitativa contundente:** en `audioi17-449d76a1` el deudor avisa que
  tiene prisa en el segundo 67 y la IA recién dice el descuento en el segundo 157.
- **H3 quedó débil** en su forma actual (tasa de empatía efectiva 0,55 vs 0,45): no titular con
  ella sin reforzarla.

---

## 4. Caveats que hay que respetar

1. **Latencia sobre diarización limpia.** En 29 % de las llamadas humanas la diarización
   colapsó a un hablante y los cambios de rol los puso el LLM, no el audio. Recalcular H1
   sobre `diarizacion_limpia == 1` antes de publicar el número.
2. **`share_palabras_agente` está contaminado** en humanos (78 % vs 80 % IA): la diarización
   atribuyó al agente turnos cortos del deudor. Verificado leyendo `audioh1-0445c357`.
   No usar como métrica de titular.
3. **Medianas y tests no paramétricos por defecto:** hay un outlier humano de 1.233 s (20 min).
4. **`n_objeciones_lex` es un proxy léxico** que subcuenta (27 % vs 43 % de llamadas con
   objeción). Debe validarse contra el etiquetado con LLM.
5. **Los audios están censurados** con un pitido sobre nombres y entidades: ninguna métrica
   puede depender de nombres propios ni de la marca de la empresa.
6. **`se_identifica` / `verifica_identidad`** detectan la *fórmula* de presentación, no la
   identificación real (imposible por la censura). Interpretar como cumplimiento de guion.

---

## 5. Pendiente

- [ ] **Etiquetado semántico con LLM** (un solo pase, cuatro variables): resultado final de la
      llamada, tipo de objeción, si el agente respondió con contraoferta concreta, y si hubo
      cierre operativo. Es el insumo que falta para responder "quién es más efectivo".
- [ ] **Notebook de análisis estadístico:** Mann-Whitney + proporciones, tamaños de efecto,
      recálculo de H1 sobre el subconjunto de diarización limpia.
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
