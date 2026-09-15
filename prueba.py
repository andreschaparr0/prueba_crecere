from faster_whisper import WhisperModel
import time

# Usamos el modelo "small" (buen balance entre español perfecto y poco peso)
# En device ponemos "cpu" con cómputo int8 para que cualquier laptop lo vuele
print("Cargando modelo...")
model = WhisperModel("small", device="cpu", compute_type="int8")

# Pon aquí la ruta de UNO de los audios de la prueba
audio_path = "C:/Users/andre/Desktop/Personal/Pruebas tecnicas/crecere/Audios/audios_humanos_censurados/0bc9a430-bdcd-44a7-a92d-e71dc33c8ad5.wav" 

inicio = time.time()
print("Transcribiendo...")
segments, info = model.transcribe(audio_path, language="es")

texto_completo = ""
for segment in segments:
    texto_completo += segment.text + " "

fin = time.time()

print("\n--- RESULTADO ---")
print(f"Idioma detectado: {info.language}")
print(f"Duración del audio: {info.duration:.2f} segundos")
print(f"Tiempo que tardó tu PC: {fin - inicio:.2f} segundos")
print("\nTexto transcrito:")
print(texto_completo)