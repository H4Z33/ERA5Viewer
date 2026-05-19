---
name: tts-qwen3-voice
description: Genera audio de voz desde texto usando Qwen3-TTS-12Hz-1.7B-CustomVoice. Soporta español, inglés y chino.
triggers: ["tts", "text to speech", "texto a voz", "Qwen3-TTS", "generar audio", "hablar", "voz", "audio generation"]
---

# INTENT
# TTS Generator Skill — Qwen3-TTS-12Hz-1.7B-CustomVoice

Genera audio de voz a partir de texto usando el modelo `Qwen3-TTS-12Hz-1.7B-CustomVoice` de HuggingFace.

## Capacidades
- Idiomas: Español, Inglés, Chino (y código ISO: es, en, zh)
- Genera archivos WAV/MP3 desde texto
- Multilingüe en una sola sesión

## Requisitos
- `transformers` library
- `torch` (CPU o CUDA)
- `scipy` para saving WAV
- Acceso a HuggingFace Hub (login con token si modelo privado)
- Suficiente RAM (modelo ~1.7B params, ~3-4GB en RAM)

## Pipeline de Uso

### Paso 1: Imports y setup
```python
from transformers import AutoModelForTextToSpeech, AutoProcessor
import torch
import scipy.io.wavfile as wavfile
import os

model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
```

### Paso 2: Cargar modelo (solo una vez)
```python
def load_tts_model():
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForTextToSpeech.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    if torch.cuda.is_available():
        model.to("cuda")
    return processor, model
```

### Paso 3: Generar audio
```python
def generate_speech(text, language="es", output_path="output.wav"):
    """
    text: string con texto a convertir
    language: "es" | "en" | "zh"
    output_path: ruta donde guardar el WAV
    """
    processor, model = load_tts_model()
    
    # Configurar idioma
    lang_code = {"es": "spanish", "en": "english", "zh": "chinese"}[language]
    
    inputs = processor(text=text, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.to("cuda") for k, v in inputs.items()}
    
    with torch.no_grad():
        audio = model.generate(
            **inputs,
            language=lang_code,
            sample_rate=12000  # 12Hz como indica el nombre del modelo
        )
    
    # Guardar WAV
    audio_np = audio.cpu().numpy().squeeze()
    wavfile.write(output_path, 12000, audio_np)
    return output_path
```

## Validación
- Verificar que el archivo WAV se creó y tiene tamaño > 0
- Verificar duración plausible (no audio vacío)
- Probar con texto corto en cada idioma

## Limitaciones
- No hace streaming de audio
- No reproduce directamente (devuelve path al archivo)
- Velocidad de generación depende de hardware

# RULES
1. [Define constraints for this skill]

# REQUIRED TOOLS
- [List tools needed]

# VALIDATION
Before completing this work, you MUST verify:
- [Define validation steps]
