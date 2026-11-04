# Guías de respuesta de cada tema (tarjeta KAN-19).
# Se usan de dos maneras:
#   1. Se le mandan a la IA junto con la duda, para que explique como queremos.
#   2. Si no hay internet o no hay clave de API, el tutor muestra la explicación base.

GUIAS = {
    "Variables y tipos de datos": {
        "explicar": (
            "Una variable es como una caja con nombre que guarda un dato mientras el programa corre. "
            "El nombre va sin espacios ni tildes y no puede empezar con un número. "
            "Los tipos básicos son int (números enteros), float (números con punto, como 7.5) "
            "y str (texto, siempre entre comillas). \"5\" es texto y 5 es un número, no son lo mismo."
        ),
        "ejemplo": 'edad = 14\nnombre = "Ana"\nprint(nombre, edad)',
        "error_tipico": "Poner espacios en el nombre de la variable o confundir \"5\" con 5.",
    },
    "print e input": {
        "explicar": (
            "print muestra algo en pantalla. input le pide un dato al usuario, y lo que va entre los "
            "paréntesis es el mensaje que ve. input siempre devuelve texto, por eso si queremos un número "
            "lo convertimos con int(input(...)) o float(input(...)). Si no, \"2\" + \"3\" da \"23\"."
        ),
        "ejemplo": 'nombre = input("¿Cómo te llamás? ")\nedad = int(input("¿Cuántos años tenés? "))\nprint("Hola", nombre, "tenés", edad, "años")',
        "error_tipico": "Sumar dos input sin int y que se peguen como texto.",
    },
    "Condicionales (if, elif, else)": {
        "explicar": (
            "if hace una pregunta que es verdadera o falsa, y si es verdadera hace lo que está adentro, "
            "con sangría. elif es otra pregunta si la primera fue falsa, y else es lo que pasa si ninguna "
            "se cumple. Para comparar se usa == (= es para guardar), y la línea del if termina con dos puntos. "
            "Con and se piden las dos condiciones y con or alcanza con una."
        ),
        "ejemplo": 'nota = int(input("Nota: "))\nif nota >= 6:\n    print("Aprobado")\nelse:\n    print("A recuperar")',
        "error_tipico": "Olvidar el else, usar = en vez de == u olvidar los dos puntos.",
    },
    "Bucles (for, while)": {
        "explicar": (
            "Un bucle repite instrucciones. for repite una cantidad fija de veces, con range(inicio, fin, salto), "
            "y el fin no se incluye. while repite mientras una condición sea verdadera, así que adentro "
            "algo tiene que cambiar para que en algún momento sea falsa, si no, no para nunca (bucle infinito). "
            "Se repite solo lo que tiene sangría."
        ),
        "ejemplo": 'for i in range(1, 11):\n    print(i)\n\ncontador = 0\nwhile contador < 3:\n    print("hola")\n    contador = contador + 1',
        "error_tipico": "Un while que nunca termina o creer que range(5) llega hasta 5.",
    },
    "Listas": {
        "explicar": (
            "Una lista guarda varios datos en orden dentro de una sola variable, entre corchetes. "
            "Las posiciones empiezan en 0. len() dice cuántos elementos tiene, append() agrega uno al final, "
            "con for se recorren uno por uno y con in se pregunta si algo está."
        ),
        "ejemplo": 'amigos = ["Ana", "Leo", "Sofi"]\nprint(amigos[0])\namigos.append("Juan")\nfor amigo in amigos:\n    print(amigo)',
        "error_tipico": "Empezar a contar en 1 o pedir una posición que no existe (IndexError).",
    },
    "Errores": {
        "explicar": (
            "El mensaje rojo dice qué tipo de error es y en qué línea. Los más comunes son SyntaxError "
            "(algo mal escrito, como dos puntos, paréntesis o comillas sin cerrar, y a veces marca la línea "
            "de abajo), IndentationError (la sangría), NameError (un nombre que no existe o está mal escrito), "
            "TypeError (mezclar texto con números), ValueError (convertir a número algo que no lo es) "
            "e IndexError (una posición de la lista que no existe)."
        ),
        "ejemplo": 'print("hola"   # SyntaxError: falta cerrar el paréntesis\nprint("hola")  # así está bien',
        "error_tipico": "Mirar solo la línea marcada, cuando a veces el problema está en la de arriba.",
    },
}

INSTRUCCIONES = (
    "Sos un tutor de Python para estudiantes de 12 a 15 años de Educación Básica Integrada en Uruguay. "
    "Respondé en español rioplatense, con voseo, en 5 líneas o menos, con palabras simples y un ejemplo "
    "de código corto. Si la duda no es de Python, decí amablemente que solo ayudás con Python. "
    "No pidas ni repitas datos personales."
)


def guia_como_texto(tema):
    """Arma el texto de la guía de un tema para mandarle a la IA."""
    g = GUIAS[tema]
    return (
        f"Tema: {tema}. Cómo explicarlo: {g['explicar']} "
        f"Ejemplo base:\n{g['ejemplo']}\nError típico a mencionar si aplica: {g['error_tipico']}"
    )
