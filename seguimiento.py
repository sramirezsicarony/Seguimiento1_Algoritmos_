
import os
import re
import time
import platform
from pypdf import PdfReader
CARPETA = "articulos"
REPETICIONES = 1000
TOP_N = 15
# -*- coding: utf-8 -*-
"""Seguimiento - Analisis de Algoritmos.
Conteo de frecuencias en abstracts + Counting / Radix / Bucket Sort."""

# --------------------------------------------------------------
# 0. ENTORNO DE EJECUCION  -> seccion 4.1 del informe
# --------------------------------------------------------------
def info_entorno():
    print("=" * 60)
    print("ENTORNO DE EJECUCION (seccion 4.1)")
    print("=" * 60)
    print("Sistema operativo :", platform.system(), platform.release())
    print("Arquitectura      :", platform.machine())
    print("Procesador        :", platform.processor())
    print("Python            :", platform.python_version())
    print("Nucleos logicos   :", os.cpu_count())
    try:
        import pypdf
        print("pypdf             :", pypdf.__version__)
    except Exception:
        pass
    print()



# ----------------------------------------------------------------
# STOP WORDS via NLTK (lista estandar, mas defendible que una lista manual)
# Requiere: pip install nltk  y luego nltk.download("stopwords") una sola vez
# ----------------------------------------------------------------
import nltk
try:
    STOP_WORDS = set(nltk.corpus.stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    STOP_WORDS = set(nltk.corpus.stopwords.words("english"))



# --------------------------------------------------------------
# 2. PREPROCESAMIENTO -> seccion 2.2 del informe
# --------------------------------------------------------------
def extraer_texto_pdf(ruta):
    lector = PdfReader(ruta)
    partes = []
    for pag in lector.pages:
        partes.append(pag.extract_text() or "")
    return chr(10).join(partes)

def extraer_abstract(texto):
    ini = re.search(r"\bAbstract\b\s*[:.-]?", texto, re.IGNORECASE)
    if not ini:
        return texto[:2500]
    resto = texto[ini.end():]
    fin = re.search(r"\b(Key\s*words|Keywords|Index\s+Terms|1\.?\s+Introduction|I\.\s+Introduction|Introduction)\b", resto, re.IGNORECASE)
    if fin:
        return resto[:fin.start()]
    return resto[:2500]

def tokenizar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-z\s-]", " ", texto)
    texto = texto.replace("-", " ")
    tokens = texto.split()
    return [t for t in tokens if (len(t) > 2 or t == "ai") and t not in STOP_WORDS]

def construir_corpus(carpeta):
    frecuencias = {}
    detalle = []
    archivos = sorted(f for f in os.listdir(carpeta) if f.lower().endswith(".pdf"))
    if not archivos:
        raise SystemExit("No se encontraron PDFs en la carpeta " + carpeta)
    for nombre in archivos:
        texto = extraer_texto_pdf(os.path.join(carpeta, nombre))
        abstract = extraer_abstract(texto)
        tokens = tokenizar(abstract)
        for t in tokens:
            frecuencias[t] = frecuencias.get(t, 0) + 1
        detalle.append((nombre, len(abstract.split()), len(tokens), len(set(tokens))))
    return list(frecuencias.items()), detalle

# --------------------------------------------------------------
# 3. ALGORITMOS NO COMPARATIVOS -> seccion 3 y Anexo A
#    Ordenan pares (termino, frecuencia) por frecuencia, ascendente y estables.
# --------------------------------------------------------------
def counting_sort(pares):
    if not pares:
        return []
    k = max(f for _, f in pares)
    conteo = [0] * (k + 1)
    for _, f in pares:
        conteo[f] += 1
    for i in range(1, k + 1):
        conteo[i] += conteo[i - 1]
    salida = [None] * len(pares)
    for i in range(len(pares) - 1, -1, -1):
        f = pares[i][1]
        conteo[f] -= 1
        salida[conteo[f]] = pares[i]
    return salida

def radix_sort(pares, base=10):
    if not pares:
        return []
    arr = list(pares)
    maximo = max(f for _, f in arr)
    exp = 1
    while maximo // exp > 0:
        cubetas = [[] for _ in range(base)]
        for par in arr:
            digito = (par[1] // exp) % base
            cubetas[digito].append(par)
        arr = [par for cubeta in cubetas for par in cubeta]
        exp *= base
    return arr

def bucket_sort(pares, n_cubetas=None):
    if not pares:
        return []
    n = len(pares)
    if n_cubetas is None:
        n_cubetas = n
    maximo = max(f for _, f in pares)
    minimo = min(f for _, f in pares)
    rango = (maximo - minimo) or 1
    cubetas = [[] for _ in range(n_cubetas)]
    for par in pares:
        idx = int((par[1] - minimo) * (n_cubetas - 1) / rango)
        cubetas[idx].append(par)
    salida = []
    for cubeta in cubetas:
        for i in range(1, len(cubeta)):
            actual = cubeta[i]
            j = i - 1
            while j >= 0 and cubeta[j][1] > actual[1]:
                cubeta[j + 1] = cubeta[j]
                j -= 1
            cubeta[j + 1] = actual
        salida.extend(cubeta)
    return salida

# --------------------------------------------------------------
# 4. MEDICION DE TIEMPOS -> seccion 4.2
# --------------------------------------------------------------
def medir(funcion, pares, repeticiones=REPETICIONES):
    funcion(list(pares))  # calentamiento, se descarta
    t0 = time.perf_counter()
    for _ in range(repeticiones):
        resultado = funcion(list(pares))
    t1 = time.perf_counter()
    total = t1 - t0
    return resultado, (total / repeticiones) * 1000, total

# --------------------------------------------------------------
# 5. PROGRAMA PRINCIPAL
# --------------------------------------------------------------
def main():
    info_entorno()
    pares, detalle = construir_corpus(CARPETA)

    print("=" * 60)
    print("CARACTERIZACION DEL CORPUS (Tabla 1, seccion 2.3)")
    print("=" * 60)
    print("Archivo".ljust(38) + "Pal.abs".rjust(9) + "Tokens".rjust(9) + "Unicos".rjust(9))
    for nombre, pal, tok, uni in detalle:
        print(nombre[:37].ljust(38) + str(pal).rjust(9) + str(tok).rjust(9) + str(uni).rjust(9))
    total_tokens = sum(d[2] for d in detalle)
    print("-" * 65)
    print("TOTAL".ljust(38) + str(sum(d[1] for d in detalle)).rjust(9) + str(total_tokens).rjust(9) + str(len(pares)).rjust(9))
    print()
    print("Documentos procesados :", len(detalle))
    print("Tokens totales (n)    :", total_tokens)
    print("Terminos unicos       :", len(pares))
    print("Frecuencia maxima (k) :", max(f for _, f in pares))
    print()

    print("=" * 60)
    print("TIEMPOS DE EJECUCION (promedio de", REPETICIONES, "ejecuciones)")
    print("=" * 60)
    resultados = {}
    for nombre, fn in (("Counting Sort", counting_sort), ("Radix Sort", radix_sort), ("Bucket Sort", bucket_sort)):
        orden, ms, total = medir(fn, pares)
        resultados[nombre] = orden
        print(nombre.ljust(16) + ("%.6f" % ms).rjust(12) + " ms   (total %.4f s)" % total)

    print()
    print("VALIDACION (seccion 6.2)")
    base_frec = [f for _, f in resultados["Counting Sort"]]
    for nombre in resultados:
        iguales = [f for _, f in resultados[nombre]] == base_frec
        print("  " + nombre.ljust(16) + "secuencia de frecuencias identica: " + str(iguales))

    print()
    print("=" * 60)
    print("TOP", TOP_N, "TERMINOS MAS FRECUENTES (seccion 5.2)")
    print("=" * 60)
    top = list(reversed(resultados["Counting Sort"]))[:TOP_N]
    print("#".ljust(5) + "Termino".ljust(25) + "Frecuencia".rjust(12))
    i = 1
    for termino, frec in top:
        print(str(i).ljust(5) + termino.ljust(25) + str(frec).rjust(12))
        i += 1

if __name__ == "__main__":
    main()
