# Prueba rápida de la IA (tarjeta KAN-14): le manda una duda a Groq y muestra la respuesta y cuánto tardó.
# Uso: python probar_groq.py   (antes hay que correr entrenar.py y poner GROQ_API_KEY)

import os
import time

from tutor import detectar, preguntar_a_la_ia

if os.getenv("TUTOR_API", "groq").lower() == "groq" and not os.getenv("GROQ_API_KEY"):
    print("No hay clave de Groq puesta, así que el tutor va a responder con la guía.")
else:
    duda = "mi while no para nunca"
    tema, seguridad = detectar(duda)
    print(f"Duda de prueba: {duda}  (tema {tema}, seguro al {seguridad:.0%})")
    inicio = time.time()
    try:
        respuesta = preguntar_a_la_ia(duda, tema)
        print(f"\nLa IA respondió en {time.time() - inicio:.1f} segundos, la meta es menos de 5.\n")
        print(respuesta)
    except Exception as error:
        print("\nLa IA no respondió. Motivo:", error)
