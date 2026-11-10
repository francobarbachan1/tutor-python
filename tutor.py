# El cerebro del tutor (tarjeta KAN-20): detecta el tema y pide la respuesta a la IA.
#
# Qué IA usar se elige con variables de entorno:
#   TUTOR_API=groq   (por defecto, gratis)  y  GROQ_API_KEY=la_clave
#   TUTOR_API=claude                        y  ANTHROPIC_API_KEY=la_clave
#   TUTOR_MODELO=nombre del modelo, si hay que cambiarlo (mirar la consola de cada servicio)
# Si no hay clave o no hay internet, el tutor muestra la explicación base de la guía.

import os
import re
import time

import joblib

from guias import GUIAS, INSTRUCCIONES, guia_como_texto, SIN_TEMA

UMBRAL = 0.45  # si el detector está menos seguro que esto, pide que reescriban la duda
# Groq dio de baja llama-3.3-70b-versatile el 16/8/2026 y recomienda openai/gpt-oss-120b.
MODELOS = {"groq": "openai/gpt-oss-120b", "claude": "claude-haiku-4-5"}

ARCHIVO_MODELO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelo.joblib")


def recargar_modelo():
    """Carga el detector guardado. Si todavía no existe, lo entrena primero."""
    global modelo
    if not os.path.exists(ARCHIVO_MODELO):
        import entrenar

        print("Todavía no hay modelo, entrenando con las dudas guardadas...", flush=True)
        inicio = time.time()
        entrenar.entrenar()
        print(f"Listo, tardó {time.time() - inicio:.1f} s.", flush=True)
    modelo = joblib.load(ARCHIVO_MODELO)


recargar_modelo()


def detectar(duda):
    """Devuelve el tema más probable y qué tan seguro está (de 0 a 1)."""
    probabilidades = modelo.predict_proba([duda])[0]
    mejor = probabilidades.argmax()
    return modelo.classes_[mejor], float(probabilidades[mejor])


# Tema relacionado (tarjeta KAN-40). La IA ya lee la duda, así que le pedimos que diga si también
# toca otro de los seis temas. El detector no cambia.
PALABRAS_DEL_TEMA = {
    "Variables y tipos de datos": ("variable", "tipos de dato"),
    "print e input": ("print", "input"),
    "Condicionales (if, elif, else)": ("condicional",),
    "Bucles (for, while)": ("bucle",),
    "Listas": ("lista",),
    "Errores": ("error",),
}


def pedido_relacionado(tema):
    """Lo que se le agrega a las instrucciones para que la IA diga el tema relacionado."""
    otros = ", ".join(t for t in GUIAS if t != tema)
    return ("Después de la explicación, en una última línea aparte, escribí \"Tema relacionado:\" y uno "
            f"de estos temas si la duda también tiene que ver con él: {otros}. Si no tiene que ver con "
            "ninguno, escribí \"Tema relacionado: ninguno\". Esa línea no cuenta para las 5 líneas.")


def leer_tema(texto):
    """Busca cuál de los seis temas nombra el texto. Devuelve None si no nombra ninguno."""
    texto = texto.lower()
    for tema in GUIAS:
        if tema.lower() in texto:
            return tema
    for tema, palabras in PALABRAS_DEL_TEMA.items():
        if any(p in texto for p in palabras):
            return tema
    return None


# "Tema relacionado: ..." con o sin negrita. A veces la IA la pone al final de un renglón y no aparte.
MARCA_RELACIONADO = re.compile(r"[*_\s]*tema relacionado[*_\s]*:?[*_\s]*(.*)$", re.IGNORECASE)


def separar_relacionado(respuesta, tema):
    """Saca de la respuesta la línea "Tema relacionado: ..." y devuelve (respuesta, tema relacionado o None)."""
    lineas = respuesta.rstrip().splitlines()
    for i in range(len(lineas) - 1, -1, -1):
        marca = MARCA_RELACIONADO.search(lineas[i])
        if marca:
            relacionado = leer_tema(marca.group(1).replace("*", "").replace("_", ""))
            antes = lineas[i][:marca.start()].rstrip()
            lineas = lineas[:i] + ([antes] if antes else []) + lineas[i + 1:]
            return "\n".join(lineas).strip(), (relacionado if relacionado != tema else None)
    return respuesta, None


def preguntar_a_la_ia(duda, tema):
    """Le manda la duda, las instrucciones y la guía del tema a la IA elegida."""
    api = os.getenv("TUTOR_API", "groq").lower()
    nombre_modelo = os.getenv("TUTOR_MODELO", MODELOS.get(api, MODELOS["groq"]))
    guia = guia_como_texto(tema) if tema else SIN_TEMA
    sistema = INSTRUCCIONES + " " + pedido_relacionado(tema) + "\n\n" + guia

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
        return {"tema": None, "seguridad": 0, "respuesta": "Escribí tu duda y tocá Preguntar.", "fuente": "tutor",
                "relacionado": None, "segundos": 0}

    tema, seguridad = detectar(duda)
    # Si el detector no está seguro, la IA responde igual pero sin la guía de un tema (KAN-49).
    if seguridad < UMBRAL:
        tema = None

    relacionado = None
    try:
        respuesta, relacionado = separar_relacionado(preguntar_a_la_ia(duda, tema), tema)
        if not respuesta:
            raise RuntimeError("La IA solo devolvió el tema relacionado")
        fuente = "ia"
    except Exception as error:
        # El motivo queda escrito en la terminal, para saber por qué no respondió la IA.
        print("No se pudo usar la IA. Motivo:", error, flush=True)
        relacionado = None
        if tema:
            g = GUIAS[tema]
            respuesta = f"{g['explicar']}\n\nEjemplo:\n```python\n{g['ejemplo']}\n```"
            fuente = "guía"
        else:
            # Sin IA y sin tema no hay guía para mostrar.
            respuesta = ("No estoy seguro de qué tema es tu duda. ¿La podés escribir de otra forma, "
                         "contando qué querés hacer o qué error te aparece?")
            fuente = "tutor"
    return {"tema": tema, "seguridad": seguridad, "respuesta": respuesta, "fuente": fuente,
            "relacionado": relacionado, "segundos": time.time() - inicio}
