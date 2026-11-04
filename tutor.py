# El cerebro del tutor (tarjeta KAN-20): detecta el tema y pide la respuesta a la IA.
#
# Qué IA usar se elige con variables de entorno:
#   TUTOR_API=groq   (por defecto, gratis)  y  GROQ_API_KEY=la_clave
#   TUTOR_API=claude                        y  ANTHROPIC_API_KEY=la_clave
#   TUTOR_MODELO=nombre del modelo, si hay que cambiarlo (mirar la consola de cada servicio)
# Si no hay clave o no hay internet, el tutor muestra la explicación base de la guía.

import os
import time

import joblib

from guias import GUIAS, INSTRUCCIONES, guia_como_texto

UMBRAL = 0.45  # si el detector está menos seguro que esto, pide que reescriban la duda
# Groq dio de baja llama-3.3-70b-versatile el 16/8/2026 y recomienda openai/gpt-oss-120b.
MODELOS = {"groq": "openai/gpt-oss-120b", "claude": "claude-haiku-4-5"}

ARCHIVO_MODELO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelo.joblib")


def recargar_modelo():
    """Carga el detector guardado. Si todavía no existe, lo entrena primero."""
    global modelo
    if not os.path.exists(ARCHIVO_MODELO):
        import entrenar

        entrenar.entrenar()
    modelo = joblib.load(ARCHIVO_MODELO)


recargar_modelo()


def detectar(duda):
    """Devuelve el tema más probable y qué tan seguro está (de 0 a 1)."""
    probabilidades = modelo.predict_proba([duda])[0]
    mejor = probabilidades.argmax()
    return modelo.classes_[mejor], float(probabilidades[mejor])


def preguntar_a_la_ia(duda, tema):
    """Le manda la duda, las instrucciones y la guía del tema a la IA elegida."""
    api = os.getenv("TUTOR_API", "groq").lower()
    nombre_modelo = os.getenv("TUTOR_MODELO", MODELOS.get(api, MODELOS["groq"]))
    sistema = INSTRUCCIONES + "\n\n" + guia_como_texto(tema)

    if api == "claude":
        import anthropic

        cliente = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY
        r = cliente.messages.create(
            model=nombre_modelo, max_tokens=400, system=sistema,
            messages=[{"role": "user", "content": duda}],
        )
        return r.content[0].text

    from groq import Groq

    cliente = Groq()  # lee GROQ_API_KEY
    opciones = {}
    if nombre_modelo.startswith("openai/gpt-oss"):
        # Este modelo piensa antes de responder. Le pedimos que piense poco (más rápido)
        # y que no mande lo que pensó, solo la respuesta.
        opciones = {"reasoning_effort": "low", "include_reasoning": False}
    r = cliente.chat.completions.create(
        model=nombre_modelo, max_completion_tokens=1024,
        messages=[{"role": "system", "content": sistema}, {"role": "user", "content": duda}],
        **opciones,
    )
    respuesta = (r.choices[0].message.content or "").strip()
    if not respuesta:
        raise RuntimeError("La IA no devolvió texto")
    return respuesta


def responder(duda):
    """Devuelve un diccionario con el tema, la seguridad, la respuesta, de dónde salió y cuánto tardó."""
    inicio = time.time()
    duda = (duda or "").strip()
    if not duda:
        return {"tema": None, "seguridad": 0, "respuesta": "Escribí tu duda y tocá Preguntar.", "fuente": "tutor", "segundos": 0}

    tema, seguridad = detectar(duda)
    if seguridad < UMBRAL:
        respuesta = ("No estoy seguro de qué tema es tu duda. ¿La podés escribir de otra forma, "
                     "contando qué querés hacer o qué error te aparece?")
        return {"tema": None, "seguridad": seguridad, "respuesta": respuesta, "fuente": "tutor",
                "segundos": time.time() - inicio}

    try:
        respuesta = preguntar_a_la_ia(duda, tema)
        fuente = "ia"
    except Exception as error:
        # El motivo queda escrito en la terminal, para saber por qué no respondió la IA.
        print("No se pudo usar la IA, se muestra la guía. Motivo:", error)
        g = GUIAS[tema]
        respuesta = f"{g['explicar']}\n\nEjemplo:\n```python\n{g['ejemplo']}\n```"
        fuente = "guía"
    return {"tema": tema, "seguridad": seguridad, "respuesta": respuesta, "fuente": fuente,
            "segundos": time.time() - inicio}
