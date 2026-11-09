# Entrena el detector de temas (tarjeta KAN-17).
# Uso: python entrenar.py
# Junta las dudas de datos/nuestras_dudas.csv (la planilla del grupo) y de datos/dudas_nuevas.csv
# (las que se catalogan o se cargan desde el tutor), mide los aciertos y guarda modelo.joblib.

import io
import json
import os
import re
from datetime import datetime
from urllib.request import urlopen

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline, make_union

from guias import GUIAS

CARPETA = os.path.dirname(os.path.abspath(__file__))
PLANILLA = os.path.join(CARPETA, "datos", "nuestras_dudas.csv")
NUEVAS = os.path.join(CARPETA, "datos", "dudas_nuevas.csv")
MODELO = os.path.join(CARPETA, "modelo.joblib")
ULTIMO = os.path.join(CARPETA, "datos", "ultimo_entrenamiento.json")
TEMAS = list(GUIAS)


def crear_modelo():
    # Mira palabras enteras y también pedazos de palabras, así entiende aunque escriban con faltas.
    lector = make_union(
        TfidfVectorizer(),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True),
    )
    # La regresión logística aprende qué palabras van con cada tema y dice qué tan segura está.
    return make_pipeline(lector, LogisticRegression(max_iter=2000, C=10))


def normalizar(texto):
    """Para comparar dudas sin importar mayúsculas ni espacios de más."""
    return " ".join(str(texto).lower().split())


# Formas cortas de escribir un tema que aparecen en la planilla.
OTROS_NOMBRES = {
    "tipos de datos": "Variables y tipos de datos",
    "variables": "Variables y tipos de datos",
    "condicionales": "Condicionales (if, elif, else)",
    "bucles": "Bucles (for, while)",
}


def normalizar_tema(tema):
    """Acepta el tema aunque esté escrito con otras mayúsculas, espacios de más o en forma corta."""
    clave = " ".join(str(tema).split()).lower()
    return {t.lower(): t for t in TEMAS}.get(clave) or OTROS_NOMBRES.get(clave, tema)


def leer_csv(archivo):
    try:
        return pd.read_csv(archivo)
    except UnicodeDecodeError:
        return pd.read_csv(archivo, encoding="latin-1")


def url_planilla():
    """El link de la planilla del grupo. Va en la configuración privada (TUTOR_PLANILLA_URL), nunca en el código."""
    return os.getenv("TUTOR_PLANILLA_URL", "").strip()


def url_csv(url):
    """Convierte el link de Google Sheets en el link que baja esa hoja como CSV."""
    hoja = re.search(r"docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)", url)
    if not hoja:
        return url
    gid = re.search(r"[#?&]gid=(\d+)", url)
    return (f"https://docs.google.com/spreadsheets/d/{hoja.group(1)}/gviz/tq?tqx=out:csv"
            f"&gid={gid.group(1) if gid else 0}")


def guardar_planilla(planilla):
    """Guarda la planilla como datos/nuestras_dudas.csv. Devuelve (dudas de los seis temas, filas en total)."""
    planilla = planilla.copy()
    planilla.columns = [str(c).strip().lower() for c in planilla.columns]
    planilla = planilla[[c for c in planilla.columns if c and not c.startswith("unnamed")]]
    if not {"duda", "tema"} <= set(planilla.columns):
        raise ValueError("La planilla tiene que tener las columnas duda y tema.")
    planilla = planilla.dropna(subset=["duda", "tema"])
    planilla["tema"] = planilla["tema"].map(normalizar_tema)
    os.makedirs(os.path.dirname(PLANILLA), exist_ok=True)
    planilla.to_csv(PLANILLA, index=False)
    return int(planilla["tema"].isin(TEMAS).sum()), len(planilla)


def traer_planilla(url=None, espera=20):
    """Baja la planilla del grupo desde Google Sheets. Tiene que poder verse con el enlace.
    Si Google no contesta en `espera` segundos, da error y se usan las dudas guardadas."""
    with urlopen(url_csv(url or url_planilla()), timeout=espera) as r:
        return guardar_planilla(pd.read_csv(io.BytesIO(r.read())))


def juntar_dudas():
    """Todas las dudas con un tema válido, sin repetidas. Si una duda está dos veces, vale la última."""
    partes = []
    for archivo in (PLANILLA, NUEVAS):
        if os.path.exists(archivo):
            d = leer_csv(archivo)
            if {"duda", "tema"} <= set(d.columns):
                partes.append(d[["duda", "tema"]])
    if not partes:
        return pd.DataFrame(columns=["duda", "tema"])
    datos = pd.concat(partes, ignore_index=True).dropna()
    datos["duda"] = datos["duda"].astype(str).str.strip()
    datos["tema"] = datos["tema"].map(normalizar_tema)
    datos = datos[(datos["duda"] != "") & datos["tema"].isin(TEMAS)]
    datos["clave"] = datos["duda"].map(normalizar)
    datos = datos.drop_duplicates("clave", keep="last").drop(columns="clave")
    return datos.reset_index(drop=True)


def leer_ultimo():
    """Lo que dio el último entrenamiento, o None si nunca se entrenó."""
    try:
        with open(ULTIMO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def entrenar():
    datos = juntar_dudas()
    conteo = datos["tema"].value_counts()
    if len(conteo) < len(TEMAS) or conteo.min() < 2:
        raise ValueError("Hacen falta al menos 2 dudas de cada uno de los 6 temas para entrenar.")

    # Validación cruzada: entrena con 4 partes, prueba con la quinta y rota.
    pliegues = StratifiedKFold(n_splits=min(5, int(conteo.min())), shuffle=True, random_state=1)
    aciertos = float(cross_val_score(crear_modelo(), datos["duda"], datos["tema"], cv=pliegues).mean())

    modelo = crear_modelo().fit(datos["duda"], datos["tema"])
    joblib.dump(modelo, MODELO)
    resultado = {
        "fecha": datetime.now().strftime("%d/%m %H:%M"),
        "dudas": len(datos),
        "aciertos": aciertos,
        "por_tema": {t: int(conteo.get(t, 0)) for t in TEMAS},
    }
    with open(ULTIMO, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=1)
    return resultado


def main():
    if url_planilla():
        try:
            validas, total = traer_planilla()
            print(f"Planilla del grupo: {total} dudas, {validas} de los seis temas.")
        except Exception as error:
            print("No se pudo traer la planilla, se usan las dudas guardadas. Motivo:", error)
    r = entrenar()
    print(f"Dudas para entrenar: {r['dudas']}")
    for tema, n in r["por_tema"].items():
        print(f"  {tema}: {n}")
    print(f"\nAciertos estimados con dudas que no vio: {r['aciertos']:.0%}")
    print("Modelo guardado en modelo.joblib")


if __name__ == "__main__":
    main()
