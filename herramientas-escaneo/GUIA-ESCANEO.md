# Guía: de fotos a pieza 3D imprimible

La app **no** hace la reconstrucción 3D en el celular: la fotogrametría necesita mucha memoria y
procesador (a veces una placa de video NVIDIA). Lo que hace la app es ayudarte a **sacar buenas fotos**
(o sacar los mejores cuadros de un video), te las da en un ZIP, y después **importa y repara** la malla
que se genera en tu PC.

```
Celular (app) ──fotos.zip──▶ PC (reconstruir.bat) ──modelo.stl──▶ App: cortar base, escalar, exportar STL
```

## 1. Sacar las fotos (en la app → 📸 Escanear)

- **Luz pareja**: día nublado, al lado de una ventana o con dos lámparas a los costados. Sin flash.
- **Objeto mate y con textura**. Lo brillante, transparente o liso de un solo color sale mal.
  Truco: talco, spray de "revelador" o cinta de papel con dibujos.
- **Fondo con detalles** (diario, mantel estampado) y el objeto quieto. Mejor moverte vos que girar el objeto.
- **Una vuelta completa cada 10–15°**, en 2 o 3 alturas (baja, media, desde arriba). 40–80 fotos.
- Cada foto tiene que compartir ~70 % con la anterior. El objeto ocupando la mayor parte del cuadro.
- Con **video**: una vuelta lenta (~30 s por vuelta). La app extrae los cuadros más nítidos.
- Los anillos verdes en pantalla marcan qué ángulos ya cubriste (usa la brújula del celular si tiene).

Después: pestaña **Exportar → Descargar ZIP** (o "Compartir" para mandarlo a la PC por Drive, WhatsApp, mail…).

## 2. Instalar los programas en la PC (una sola vez)

Necesitás **Python 3** (https://www.python.org/downloads/ — tildá *"Add python.exe to PATH"*) y **una** de estas opciones:

| Opción | Necesita | Calidad | Descarga |
|---|---|---|---|
| **A. COLMAP + OpenMVS** (recomendada) | Cualquier PC (GPU opcional) | Muy buena | COLMAP: https://github.com/colmap/colmap/releases — OpenMVS: https://github.com/cdcseacave/openMVS/releases |
| **B. Meshroom** | GPU NVIDIA | Muy buena, más simple | https://alicevision.org/#meshroom |
| **C. Solo COLMAP** | GPU NVIDIA | Buena | https://github.com/colmap/colmap/releases |

Descomprimí cada programa en `C:\COLMAP`, `C:\OpenMVS` o `C:\Meshroom` (el script los busca ahí),
o definí las variables de entorno `COLMAP_EXE`, `OPENMVS_DIR` o `MESHROOM_BATCH`.

## 3. Reconstruir

- **Windows**: poné `reconstruir.bat` y `reconstruir.py` en la misma carpeta y **arrastrá el ZIP encima de `reconstruir.bat`**.
- O desde una terminal:

```
python reconstruir.py escaneo.zip                       # elige el método solo
python reconstruir.py escaneo.zip --metodo openmvs --calidad alta
python reconstruir.py escaneo.zip --video               # si las fotos salieron de un video
python reconstruir.py escaneo.zip --sin-gpu             # PC sin placa NVIDIA
python reconstruir.py escaneo.zip --tamano 80           # la medida mayor queda en 80 mm
python reconstruir.py --solo-posproceso malla.ply       # solo limpiar una malla y pasarla a STL
```

Tarda entre 5 minutos y más de 1 hora según la PC y la cantidad de fotos.
El resultado queda en `escaneo_resultado\modelo.stl`. Los archivos intermedios quedan en `escaneo_trabajo\` (los podés borrar).

## 4. Importar y dejarlo listo para imprimir (en la app)

1. **Archivo → Importar malla** (STL, OBJ o PLY). Si la malla está cerrada aparece como sólido ✔.
2. **Cortar por plano**: aplana la base (y elimina la mesa/el piso que a veces aparece).
3. **Ajustar tamaño**: la fotogrametría no conoce la escala real. Medí tu objeto con una regla y escribí esa medida.
4. Si la malla vino con agujeros: **Envolvente convexa** (solo para formas simples) o repará con Blender
   (*3D Print Toolbox → Make Manifold*) o Meshmixer, y volvé a importar.
5. **Simplificar** si pesa mucho, y **⬇ STL**.

## Alternativas en la nube (sin PC potente)

Apps como **Polycam**, **KIRI Engine**, **RealityScan** o **Luma AI** procesan las fotos en sus servidores y
exportan OBJ/STL, que podés importar en la app. Muchas tienen un plan gratis con límites. No están integradas
para no guardar claves de API dentro de la app; si en el futuro querés integrarlas, la clave debería quedar en
un servidor propio, nunca en el código de la app.

## Problemas comunes

- *"COLMAP no pudo ubicar las cámaras"*: pocas fotos, poca superposición o el objeto no tiene textura.
- *Sale una mancha deforme*: el objeto se movió, era brillante o el fondo era liso.
- *Falta la parte de abajo*: es normal; cortala con "Cortar por plano" o escaneá el objeto dado vuelta y uní ambas mallas.
