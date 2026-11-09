# La pantalla del tutor (tarjeta KAN-21).
# Uso: streamlit run app.py   (se abre en el navegador)
#
# Con el "Modo equipo" prendido (barra de la izquierda) aparecen las herramientas del grupo:
#   - catalogar cada duda que se prueba, eligiendo el tema que era de verdad
#   - cargar dudas a mano
#   - ver y corregir las dudas nuevas, pasarlas a la planilla y volver a entrenar el detector
# Las dudas nuevas se guardan en datos/dudas_nuevas.csv. Para mostrárselo a los estudiantes, apagar el modo equipo.

import os
import time
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Tutor de Python", page_icon="🐍")

# En la web (Streamlit Community Cloud) la configuración privada llega en st.secrets:
# GROQ_API_KEY, TUTOR_PLANILLA_URL y TUTOR_CONTRASENA_EQUIPO. Se pasan al entorno para que
# tutor.py y entrenar.py las lean igual que en la compu. Nada de esto va en el código.
try:
    for nombre, valor in st.secrets.items():
        if isinstance(valor, str):
            os.environ.setdefault(nombre, valor)
except Exception:
    pass  # en la compu no hay secrets, se usan las variables de entorno

print("Arrancando el tutor...", flush=True)
import entrenar  # noqa: E402
import tutor  # noqa: E402
from guias import GUIAS  # noqa: E402

TEMAS = list(GUIAS)
NINGUNO = "No es de ningún tema"
NO_SABIA = "No sabía"
COLUMNAS = ["duda", "tema", "dijo_el_tutor", "seguro_al", "acerto", "como", "escrita_por", "fecha"]
META_POR_TEMA = 40  # KAN-13: al menos 40 dudas por tema
CONTRASENA_EQUIPO = os.getenv("TUTOR_CONTRASENA_EQUIPO", "")


@st.cache_resource(show_spinner="Preparando el tutor con la planilla del grupo...")
def preparar_web():
    """Si hay link de la planilla, al arrancar la trae y entrena una vez. En la compu no hace nada."""
    if not entrenar.url_planilla():
        return None
    try:
        inicio = time.time()
        print("Trayendo la planilla del grupo...", flush=True)
        entrenar.traer_planilla()
        print(f"Planilla traída en {time.time() - inicio:.1f} s, entrenando...", flush=True)
        res = entrenar.entrenar()
        print(f"Entrenado en {time.time() - inicio:.1f} s desde que arrancó.", flush=True)
        tutor.recargar_modelo()
        estado = f"Al arrancar se entrenó con la planilla del grupo, {res['dudas']} dudas."
    except Exception as error:
        estado = f"No se pudo traer la planilla al arrancar, se usan las dudas guardadas. Motivo: {error}"
    print(estado, flush=True)
    return estado


estado_web = preparar_web()


# ---------- Dudas nuevas (datos/dudas_nuevas.csv) ----------

def leer_nuevas():
    if os.path.exists(entrenar.NUEVAS):
        d = entrenar.leer_csv(entrenar.NUEVAS)
        for c in COLUMNAS:
            if c not in d.columns:
                d[c] = ""
        return d[COLUMNAS].fillna("")
    return pd.DataFrame(columns=COLUMNAS)


def escribir_nuevas(d):
    d = d.copy()
    d["duda"] = d["duda"].astype(str).str.strip()
    d = d[d["duda"] != ""]
    # Acertó si dijo el tema correcto, o si no sabía y la duda no era de ningún tema.
    d["acerto"] = [
        (t == NINGUNO and dijo == NO_SABIA) or (t != NINGUNO and t == dijo)
        for t, dijo in zip(d["tema"], d["dijo_el_tutor"])
    ]
    os.makedirs(os.path.dirname(entrenar.NUEVAS), exist_ok=True)
    d[COLUMNAS].to_csv(entrenar.NUEVAS, index=False)


def nueva_fila(duda, tema, como):
    """Anota lo que dice el tutor ANTES de aprender la duda, así el acierto es honesto."""
    detectado, seguridad = tutor.detectar(duda)
    dijo = NO_SABIA if seguridad < tutor.UMBRAL else detectado
    return {
        "duda": duda, "tema": tema, "dijo_el_tutor": dijo, "seguro_al": round(seguridad, 2),
        "acerto": "", "como": como, "escrita_por": st.session_state.get("nombre", "").strip(),
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def agregar_nuevas(filas):
    escribir_nuevas(pd.concat([leer_nuevas(), pd.DataFrame(filas)], ignore_index=True))


# ---------- Barra lateral ----------

with st.sidebar:
    # En la compu arranca prendido. En la web arranca apagado y pide la contraseña del equipo.
    modo_equipo = st.toggle("Modo equipo", value=not CONTRASENA_EQUIPO,
                            help="Muestra las herramientas para catalogar dudas y volver a entrenar. "
                                 "Apagalo para mostrarle el tutor a los estudiantes.")
    if modo_equipo and CONTRASENA_EQUIPO:
        escrita = st.text_input("Contraseña del equipo", type="password", key="contrasena")
        modo_equipo = escrita == CONTRASENA_EQUIPO
        if escrita and not modo_equipo:
            st.error("Esa no es la contraseña del equipo.")
    if modo_equipo:
        st.text_input("Tu nombre", key="nombre", help="Se anota en la columna escrita por de la planilla.")
        ultimo = entrenar.leer_ultimo()
        if ultimo:
            st.caption(f"Último entrenamiento: {ultimo['fecha']}, con {ultimo['dudas']} dudas. "
                       f"Acierta alrededor del {ultimo['aciertos']:.0%}.")
        if estado_web:
            st.caption(estado_web)

st.title("Tutor de Python")

if modo_equipo:
    tab_tutor, tab_cargar, tab_dudas = st.tabs(["Tutor", "Cargar dudas", "Dudas y entrenamiento"])
else:
    tab_tutor = st.container()


# ---------- Tutor ----------

with tab_tutor:
    st.write("Escribí tu duda con tus palabras, como si se la preguntaras a un profe. "
             "No pongas tu nombre ni datos personales.")
    duda = st.text_area("Tu duda", placeholder="Por ejemplo: mi while no para nunca")

    if st.button("Preguntar", type="primary"):
        with st.spinner("Pensando..."):
            resultado = tutor.responder(duda)
        st.session_state.resultado = {**resultado, "duda": (duda or "").strip()}
        st.session_state.pregunta_n = st.session_state.get("pregunta_n", 0) + 1
        st.session_state.guardada = False

    r = st.session_state.get("resultado")
    if r:
        if r["tema"]:
            st.caption(f"Tema: {r['tema']}" + (f", seguro al {r['seguridad']:.0%}" if modo_equipo else ""))
        st.markdown(r["respuesta"])
        if r["fuente"] == "guía":
            st.caption("Respuesta de la guía, porque no se pudo conectar con la IA.")
        elif r["fuente"] == "ia":
            st.caption("Esta respuesta la escribió una inteligencia artificial y puede tener errores.")
        relacionado = r.get("relacionado")
        if relacionado in GUIAS:
            st.info(f"**Esto también tiene que ver con {relacionado}.** {GUIAS[relacionado]['explicar']}")

        if modo_equipo and r["duda"]:
            st.divider()
            st.subheader("Catalogar esta duda")
            st.caption("Elegí el tema que era de verdad. Queda guardada para que el tutor la aprenda "
                       "la próxima vez que lo entrenes.")
            n = st.session_state.get("pregunta_n", 0)
            tema = st.radio("Tema de verdad", TEMAS + [NINGUNO], index=None, key=f"tema_{n}")
            if st.session_state.get("guardada"):
                st.success("Duda guardada.")
            elif st.button("Guardar duda", disabled=tema is None, key=f"guardar_{n}"):
                agregar_nuevas([nueva_fila(r["duda"], tema, "Catalogada al probar el tutor")])
                st.session_state.guardada = True
                st.rerun()


# ---------- Cargar dudas a mano ----------

def guardar_a_mano():
    lineas = [x.strip() for x in st.session_state.get("carga_texto", "").splitlines() if x.strip()]
    tema = st.session_state.get("carga_tema")
    if not lineas:
        st.session_state.carga_aviso = ("warning", "Escribí al menos una duda.")
    elif not tema:
        st.session_state.carga_aviso = ("warning", "Elegí el tema de esas dudas.")
    else:
        agregar_nuevas([nueva_fila(x, tema, "Cargada a mano en el tutor") for x in lineas])
        st.session_state.carga_texto = ""
        st.session_state.carga_aviso = ("success", f"Guardé {len(lineas)} dudas de {tema}. Para que el tutor "
                                                   "las aprenda, entrenalo en la pestaña Dudas y entrenamiento.")


if modo_equipo:
    with tab_cargar:
        st.subheader("Cargar dudas a mano")
        st.write("Escribí una duda por renglón, como la escribiría un estudiante que recién empieza, "
                 "con sus palabras y hasta con errores. Después elegí el tema de todas.")
        st.text_area("Dudas, una por renglón", height=200, key="carga_texto")
        st.selectbox("Tema", TEMAS, index=None, placeholder="Elegí el tema", key="carga_tema")
        st.button("Guardar dudas", type="primary", on_click=guardar_a_mano)
        aviso = st.session_state.pop("carga_aviso", None)
        if aviso:
            getattr(st, aviso[0])(aviso[1])


# ---------- Dudas y entrenamiento ----------

if modo_equipo:
    with tab_dudas:
        nuevas = leer_nuevas()
        todas = entrenar.juntar_dudas()

        st.subheader("Cómo venimos")
        c1, c2, c3 = st.columns(3)
        c1.metric("Dudas para entrenar", len(todas))
        c2.metric("Dudas nuevas", len(nuevas))
        if len(nuevas):
            bien = int(nuevas["acerto"].astype(str).str.lower().eq("true").sum())
            c3.metric("Acertó en las nuevas", f"{bien / len(nuevas):.0%}",
                      help="Cuántas acertó antes de aprenderlas. Es la prueba más honesta. La meta es 80%.")
        por_tema = todas["tema"].value_counts()
        tabla = pd.DataFrame({"Tema": TEMAS, "Dudas": [int(por_tema.get(t, 0)) for t in TEMAS]})
        st.dataframe(tabla, hide_index=True, width="stretch", column_config={
            "Dudas": st.column_config.ProgressColumn(f"Dudas (meta {META_POR_TEMA})", min_value=0,
                                                     max_value=META_POR_TEMA, format="%d")})

        st.subheader("Volver a entrenar")
        st.write("Entrena el detector con las dudas de la planilla más las nuevas, y lo deja andando en el tutor.")
        if st.button("Entrenar con todas las dudas", type="primary"):
            antes = entrenar.leer_ultimo()
            try:
                with st.spinner("Entrenando..."):
                    res = entrenar.entrenar()
                    tutor.recargar_modelo()
                texto = f"Listo. Aprendió con {res['dudas']} dudas y acierta alrededor del {res['aciertos']:.0%}"
                if antes:
                    texto += f" (antes {antes['aciertos']:.0%}, con {antes['dudas']} dudas)"
                st.success(texto + ".")
            except ValueError as error:
                st.error(str(error))

        st.subheader("Dudas nuevas")
        if len(nuevas):
            st.caption("Podés corregir el tema o borrar una fila (seleccionala y tocá el tacho). "
                       "Después tocá Guardar cambios.")
            editado = st.data_editor(
                nuevas, hide_index=True, num_rows="dynamic", width="stretch", key="editor",
                column_order=["duda", "tema", "dijo_el_tutor", "escrita_por", "fecha"],
                column_config={
                    "duda": st.column_config.TextColumn("Duda", width="large"),
                    "tema": st.column_config.SelectboxColumn("Tema de verdad", options=TEMAS + [NINGUNO],
                                                             required=True),
                    "dijo_el_tutor": st.column_config.TextColumn("Dijo el tutor", disabled=True),
                    "escrita_por": st.column_config.TextColumn("Escrita por"),
                    "fecha": st.column_config.TextColumn("Fecha", disabled=True),
                })
            if st.button("Guardar cambios"):
                escribir_nuevas(editado.fillna(""))
                st.success("Cambios guardados.")
                st.rerun()

            st.subheader("Pasarlas a la planilla")
            st.write("Para juntarlas con las del grupo, copiá este bloque con el botón de copiar "
                     "(arriba a la derecha del bloque) y pegalo en la planilla, en la primera fila vacía.")
            para_planilla = nuevas[nuevas["tema"] != NINGUNO]
            filas = [[str(x.duda).replace("\t", " "), x.tema, x.como, x.escrita_por, ""]
                     for x in para_planilla.itertuples()]
            st.code("\n".join("\t".join(f) for f in filas), language=None)
        else:
            st.info("Todavía no hay dudas nuevas. Catalogalas en la pestaña Tutor o cargalas en Cargar dudas.")

        st.subheader("Traer la planilla del grupo")

        def quitar_ya_cargadas():
            """Saca de las nuevas las que ya están en la planilla, para no repetirlas. Devuelve cuántas sacó."""
            ya = set(entrenar.leer_csv(entrenar.PLANILLA)["duda"].map(entrenar.normalizar))
            quedan = nuevas[~nuevas["duda"].map(entrenar.normalizar).isin(ya)]
            escribir_nuevas(quedan)
            return len(nuevas) - len(quedan)

        def avisar(validas, total, sacadas):
            texto = f"La planilla tiene {total} dudas y {validas} son de los seis temas."
            if sacadas:
                texto += f" Saqué {sacadas} dudas nuevas que ya estaban en la planilla."
            if validas < total:
                texto += (f" Las otras {total - validas} tienen un tema que no es ninguno de los seis "
                          "y no se usan.")
            return texto

        if entrenar.url_planilla():
            st.write("Baja las dudas que el grupo cargó en la planilla y vuelve a entrenar el tutor.")
            if st.button("Traer la planilla y entrenar", type="primary"):
                try:
                    with st.spinner("Trayendo la planilla y entrenando..."):
                        validas, total = entrenar.traer_planilla()
                        sacadas = quitar_ya_cargadas()
                        res = entrenar.entrenar()
                        tutor.recargar_modelo()
                    st.success(avisar(validas, total, sacadas)
                               + f" Ahora acierta alrededor del {res['aciertos']:.0%}.")
                except Exception as error:
                    st.error(f"No se pudo traer la planilla. Motivo: {error}")
        else:
            st.write("Cuando el grupo haya sumado dudas en la planilla, bajala desde Google Sheets con "
                     "Archivo, Descargar, Valores separados por comas (.csv), y subí ese archivo acá.")
            archivo = st.file_uploader("Planilla en CSV", type="csv")
            if archivo is not None and st.button("Usar esta planilla"):
                try:
                    try:
                        planilla = pd.read_csv(archivo)
                    except UnicodeDecodeError:
                        archivo.seek(0)
                        planilla = pd.read_csv(archivo, encoding="latin-1")
                    validas, total = entrenar.guardar_planilla(planilla)
                    st.success(avisar(validas, total, quitar_ya_cargadas())
                               + " Ahora tocá Entrenar con todas las dudas.")
                except ValueError as error:
                    st.error(str(error))
