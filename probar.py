# Prueba el tutor con dudas que el modelo nunca vio (tarjetas KAN-23 y KAN-24).
# Uso: python probar.py datos/dudas_companeros.csv
# El archivo tiene que tener las columnas duda y tema (el tema revisado por nosotros).
# Mide los aciertos del detector y cuánto tarda cada respuesta.

import sys

import pandas as pd

from tutor import detectar, responder


def main(archivo, con_ia=True, cuantas_cronometrar=10):
    datos = pd.read_csv(archivo).dropna(subset=["duda", "tema"])
    aciertos = 0
    for _, fila in datos.iterrows():
        tema, seguridad = detectar(fila["duda"])
        acerto = tema == fila["tema"]
        aciertos += acerto
        if not acerto:
            print(f"FALLÓ  [{fila['tema']} → {tema} ({seguridad:.0%})]  {fila['duda']}")
    print(f"\nAciertos del detector: {aciertos} de {len(datos)} ({aciertos / len(datos):.0%})")
    print("Meta del requerimiento 1: 8 de cada 10 (80%)")

    if con_ia:
        tiempos = [responder(d)["segundos"] for d in datos["duda"].head(cuantas_cronometrar)]
        print(f"\nTiempo promedio de respuesta: {sum(tiempos) / len(tiempos):.1f} s (meta: menos de 5 s)")
        print(f"Respuesta más lenta: {max(tiempos):.1f} s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "datos/dudas_companeros.csv")
