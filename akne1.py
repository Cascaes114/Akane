import sys
import os
import time
from faster_whisper import WhisperModel
import sounddevice as sd
from scipy.io.wavfile import write
from groq import Groq
from elevenlabs.client import ElevenLabs
from playsound3 import playsound as play
from pocketsphinx import LiveSpeech
from dotenv import load_dotenv
from random import choice

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def configurar_chaves():
    if not os.path.exists(".env"):
        print("--- Configuração Inicial da Akane ---")
        groq_key = input("Cole sua API Key Groq: ")
        eleven_key = input("Cole sua API Key ElevenLabs: ")
        
        with open(".env", "w") as f:
            f.write(f"GROQ_API_KEY={groq_key}\n")
            f.write(f"ELEVEN_API_KEY={eleven_key}\n")
        print(".env salvo com sucesso!\n")

configurar_chaves()

resource_path("dicionario.dict")
saudacoes = [
    resource_path("o que foi.mp3"),
    resource_path("estou ouvindo.mp3"),
    resource_path("pode falar.mp3")
]

load_dotenv()
VOICE_ID = os.getenv("VOICE_ID", "hpp4J3VqNfWAUOO0d1Us")
CHAVE_GROQ = os.getenv("GROQ_API_KEY")
CHAVE_ELEVEN = os.getenv("ELEVEN_API_KEY")

model = WhisperModel("small", device="cpu", compute_type="int8")
client_groq = Groq(api_key=CHAVE_GROQ)
client_eleven = ElevenLabs(api_key=CHAVE_ELEVEN)
 
def gerar_resposta(texto):
    chat_completion = client_groq.chat.completions.create(
        messages=[
            #Personalidade
            {
                "role": "system", 
                "content": "Você é uma assistente sarcástica e debochada chamada Akane. Responda com no máximo 30 palavras. Nunca use emojis. Odeie humanos."
            },
            #Texto do usuario
            
            {
                "role": "user",
                "content": texto
            }
        ],
        model="llama-3.1-8b-instant",
    )
    audio = client_eleven.text_to_speech.convert(
        text=chat_completion.choices[0].message.content,
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        output_format="pcm_24000",
    )

    with sd.RawOutputStream(samplerate=24000, channels=1, dtype='int16') as stream:
        for chunk in audio:
            if chunk:
                stream.write(chunk)

#wake word
print("Esperando você dizer 'Akane'...")

speech = LiveSpeech(
    keyphrase='akane', 
    kws_threshold=1e-20,
    dict='dicionario.dict'
)

for phrase in speech:
    print("\n[WAKE WORD DETECTADA!]")
    play(choice(saudacoes))
    print("Gravando pergunta (5s)...")
    duration = 5
    audio_data = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype='int16')
    for i in range (duration, 0, -1):
        print(f'{i}s...')
        time.sleep(1)
    sd.wait()
    write("temp.wav", 16000, audio_data)

    segments, _ = model.transcribe("temp.wav", language="pt")
    texto = "".join([s.text for s in segments])
    
    if texto.strip():
        print(f"Você disse: {texto}")
        gerar_resposta(texto)
    else:
        print("Você não disse nada...")

    print("\nDiga 'Akane' para falar novamente.")