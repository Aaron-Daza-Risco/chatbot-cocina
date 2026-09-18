import os
import tempfile

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


# -------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# -------------------------------------------------

st.set_page_config(
    page_title="Chatbot de comida peruana",
    page_icon="🍲",
    layout="centered"
)


# -------------------------------------------------
# 2. CARGAR LA CLAVE DE GROQ
# -------------------------------------------------

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("No se encontró GROQ_API_KEY en el archivo .env")
    st.stop()


# Cliente compatible con OpenAI, conectado a Groq
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)


# -------------------------------------------------
# 3. TÍTULO
# -------------------------------------------------

st.title("🍲 Chatbot de comida peruana")

st.caption(
    "Realiza consultas escribiendo o cargando un archivo de audio."
)


# -------------------------------------------------
# 4. PROMPT DEL SISTEMA
# -------------------------------------------------

SYSTEM_PROMPT = """
Eres un asistente especializado en gastronomía peruana.

Responde únicamente consultas relacionadas con comida peruana:
platos, ingredientes, regiones, preparación, historia culinaria
y recomendaciones gastronómicas.

Si la pregunta no corresponde al tema, indícalo cordialmente
y orienta al usuario a formular una consulta sobre gastronomía peruana.

Responde en español y con explicaciones claras para estudiantes.
"""


# -------------------------------------------------
# 5. MEMORIA DE LA CONVERSACIÓN
# -------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# Mostrar mensajes anteriores
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -------------------------------------------------
# 6. FUNCIÓN PARA CONSULTAR AL CHATBOT
# -------------------------------------------------

def consultar_chatbot():

    historial = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    historial.extend(st.session_state.messages)

    respuesta = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=historial
    )

    return respuesta.choices[0].message.content


# -------------------------------------------------
# 7. PARTE 1: CONSULTA MEDIANTE TEXTO
# -------------------------------------------------

pregunta = st.chat_input(
    "Escribe una pregunta sobre comida peruana"
)


if pregunta:

    # Guardar pregunta
    st.session_state.messages.append(
        {
            "role": "user",
            "content": pregunta
        }
    )

    # Mostrar pregunta
    with st.chat_message("user"):
        st.markdown(pregunta)


    # Generar respuesta
    with st.chat_message("assistant"):

        with st.spinner("Generando respuesta..."):

            try:

                respuesta = consultar_chatbot()

                st.markdown(respuesta)

                # Guardar respuesta
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": respuesta
                    }
                )

            except Exception as error:

                st.error(
                    f"Ocurrió un error: {error}"
                )


# -------------------------------------------------
# 8. PARTE 2: CONSULTA MEDIANTE AUDIO
# -------------------------------------------------

st.divider()

st.subheader("🎤 Consulta mediante audio")

st.write(
    "Carga un archivo de audio con una pregunta sobre comida peruana."
)


audio = st.file_uploader(
    "Selecciona un archivo",
    type=["mp3", "wav", "m4a", "webm"]
)


# Comprobar si el usuario cargó un audio
if audio is not None:

    # Mostrar reproductor
    st.audio(audio)

    # Botón para procesar el audio
    if st.button("🎤 Transcribir y consultar"):

        extension = audio.name.split(".")[-1]


        # -----------------------------------------
        # Crear archivo temporal
        # -----------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{extension}"
        ) as archivo_temp:

            archivo_temp.write(
                audio.getbuffer()
            )

            ruta_temp = archivo_temp.name


        try:

            # -----------------------------------------
            # 9. TRANSCRIBIR AUDIO CON WHISPER
            # -----------------------------------------

            with st.spinner(
                "Transcribiendo audio con Whisper..."
            ):

                with open(
                    ruta_temp,
                    "rb"
                ) as archivo_audio:

                    transcripcion = (
                        client.audio.transcriptions.create(
                            model="whisper-large-v3-turbo",
                            file=archivo_audio,
                            language="es"
                        )
                    )


            texto = transcripcion.text


            # -----------------------------------------
            # 10. MOSTRAR TRANSCRIPCIÓN
            # -----------------------------------------

            st.success(
                "✅ Audio transcrito correctamente."
            )

            st.write(
                "**Texto transcrito:**"
            )

            st.info(texto)


            # -----------------------------------------
            # 11. GUARDAR TEXTO COMO PREGUNTA
            # -----------------------------------------

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": texto
                }
            )


            # Mostrar mensaje transcrito
            with st.chat_message("user"):

                st.markdown(
                    f"🎤 {texto}"
                )


            # -----------------------------------------
            # 12. ENVIAR TRANSCRIPCIÓN AL CHATBOT
            # -----------------------------------------

            with st.chat_message("assistant"):

                with st.spinner(
                    "Generando respuesta..."
                ):

                    respuesta = consultar_chatbot()


                st.markdown(respuesta)


            # Guardar respuesta
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": respuesta
                }
            )


        except Exception as error:

            st.error(
                f"Ocurrió un error procesando el audio: {error}"
            )


        finally:

            # -----------------------------------------
            # 13. BORRAR ARCHIVO TEMPORAL
            # -----------------------------------------

            if os.path.exists(ruta_temp):

                os.remove(ruta_temp)


# -------------------------------------------------
# 14. LIMPIAR CONVERSACIÓN
# -------------------------------------------------

st.divider()

if st.button("🗑️ Limpiar conversación"):

    st.session_state.messages = []

    st.rerun()