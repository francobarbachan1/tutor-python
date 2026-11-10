# Tutor de Python

Trabajo final de Ingeniería de Software, CeRP del Sur. Grupo: Camila Cuitiño, Mauricio Fernández, Axel Madruga y Franco Barbachan.

Es un tutor para estudiantes de 12 a 15 años de EBI que están aprendiendo Python. El estudiante escribe su duda con sus palabras. Un detector que entrenamos con nuestras propias dudas reconoce el tema, y una IA escribe la explicación siguiendo la guía que armamos para ese tema.

## Probarlo

- **En la web**, con el link que da Streamlit, cuando esté publicado (ver más abajo).
- **En una compu con Windows**, se baja el repositorio (botón verde Code, Download ZIP), se descomprime y se hace doble clic en `abrir_tutor.bat`. La primera vez instala Python y las librerías si faltan. Después pide la clave de Groq. Si no hay clave, se toca Enter y el tutor responde con la guía.
- **A mano**, en cualquier sistema, con `pip install -r requirements.txt` y después `streamlit run app.py`.

## Dónde se cargan las dudas

Todas las dudas del grupo van a la planilla "Dudas para entrenar, tutor IA" en el Drive. El tutor tiene un **Modo equipo** (barra de la izquierda) con tres pestañas:

- **Tutor.** Después de cada respuesta se elige el tema que era de verdad y se guarda la duda. Queda anotado qué dijo el tutor antes de aprenderla, así se mide cuánto acierta con dudas que no vio.
- **Cargar dudas.** Se escriben varias dudas, una por renglón, y se elige el tema.
- **Dudas y entrenamiento.** Muestra cuántas dudas hay por tema, permite corregir las nuevas, arma un bloque para pegar en la planilla y vuelve a entrenar. En la web tiene el botón **Traer la planilla y entrenar**, que baja la planilla y entrena con un clic.

En la compu el Modo equipo arranca prendido. En la web arranca apagado y pide la contraseña del equipo, así los estudiantes ven solo el tutor.

## Cómo funciona por dentro

- **Detector de temas** (`entrenar.py`). Aprende de nuestras dudas qué palabras van con cada tema. Mira palabras enteras y pedazos de palabras, así entiende aunque escriban con faltas. Usa scikit-learn (TF-IDF y regresión logística). Si está menos de 45% seguro, la IA responde igual pero sin la guía de un tema, y si no es de Python dice que solo ayuda con Python (KAN-49). Si además no hay IA, pide que reescriban la duda.
- **IA que escribe** (`tutor.py`). Recibe las instrucciones (tutor para estudiantes de 12 a 15 años, 5 líneas o menos, con un ejemplo) y la guía del tema (`guias.py`). Usa Groq, que es gratis, con el modelo openai/gpt-oss-120b. Se puede cambiar a Claude. Si no hay clave o no hay internet, muestra la explicación de la guía. La IA también dice si la duda toca otro de los seis temas, y en ese caso el tutor agrega abajo "Esto también tiene que ver con..." con la explicación corta de ese tema (KAN-40).
- **Pantalla** (`app.py`). Está hecha con Streamlit.

| Archivo | Para qué sirve | Tarjeta |
|---|---|---|
| app.py | La pantalla del tutor | KAN-21 y KAN-31 |
| tutor.py | Detecta el tema y le pide la respuesta a la IA | KAN-20 |
| entrenar.py | Entrena el detector y mide los aciertos | KAN-17 |
| guias.py | Cómo se explica cada tema | KAN-19 |
| probar.py | Prueba el tutor con dudas que nunca vio | KAN-23 y KAN-24 |
| probar_groq.py | Prueba rápida de que la IA responde y cuánto tarda | KAN-14 |
| abrir_tutor.bat | Hace todo solo en Windows | KAN-21 |
| datos/nuestras_dudas.csv | Copia de las dudas con su tema, para entrenar sin internet | KAN-13 |

## Cómo trabajar con GitHub

No hace falta saber comandos. Se puede hacer todo desde VS Code.

**La primera vez**
1. Crearse una cuenta en [github.com](https://github.com) y pasarle el usuario a Franco.
2. Aceptar la invitación al repositorio que llega por mail.
3. En VS Code, abrir Source Control (el ícono de las ramitas, a la izquierda), tocar **Clone Repository** y pegar `https://github.com/francobarbachan1/tutor-python`. Elegir una carpeta. VS Code pide iniciar sesión en GitHub.

**Cada vez que se cambia algo**
1. Antes de empezar, tocar **Sync Changes** (o el botón de las flechitas abajo a la izquierda) para traer lo último que subieron los demás.
2. Hacer los cambios y guardar.
3. En Source Control, escribir en el cuadro de mensaje qué se cambió, por ejemplo "Mejoro la guía de Errores".
4. Tocar **Commit** y después **Sync Changes**. Listo, ya lo ven todos.

**Sin instalar nada.** En github.com se abre el archivo, se toca el lápiz, se cambia y se toca **Commit changes**.

**Reglas del grupo.** Avisar en el grupo qué archivo se va a tocar, para no pisarse. Escribir mensajes que digan qué se cambió. Nunca subir la clave de Groq ni el link de la planilla.

## Cómo está publicado en la web

Streamlit es la librería con la que está hecha la pantalla del tutor. **Streamlit Community Cloud** es un servicio gratis de la misma empresa: toma el código de este repositorio, lo corre en sus computadoras y da un link para usarlo desde cualquier navegador. Cada vez que alguien sube un cambio a GitHub, la web se actualiza sola, pero solo recarga `app.py`. Si el cambio es en `tutor.py`, `entrenar.py` o `guias.py`, hay que reiniciarla desde Manage app, Reboot app, para que tome el código nuevo. La web está en https://tutor-python-cerp.streamlit.app/

Para publicarlo (una sola vez):
1. Entrar a [share.streamlit.io](https://share.streamlit.io) con la cuenta de GitHub.
2. Tocar **Create app**, elegir el repositorio `francobarbachan1/tutor-python`, la rama `main` y el archivo `app.py`.
3. En **Advanced settings**, en **Secrets**, pegar las tres líneas de `.streamlit/secrets.example.toml` con los valores de verdad: la clave de Groq, el link de la planilla y una contraseña para el Modo equipo.
4. Tocar **Deploy**.

Lo que se guarda en la web se borra cuando se reinicia. Por eso las dudas se cargan en la planilla, y la web la trae cada vez que arranca.

## Estado al 4/11

La planilla tiene 177 dudas, 60 de Franco, 60 de Camila y 57 de Axel. Se usan 164, porque 13 son de Funciones y Avanzado, que no están entre los seis temas. Con las 164 el detector acierta alrededor del 66% de las dudas que no vio. Con las 74 de antes era 51%. Los temas que más le cuestan son print e input y Errores. La meta es 80%.
