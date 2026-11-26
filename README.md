# 🐶 Perrito Widget

Un labrador negro chiquito para el escritorio de Windows 11 que teclea y mueve el mouse contigo.

- ⌨️ Al presionar una tecla levanta la patita izquierda o derecha (según la tecla).
- ⚡ Si tecleas rápido usa las dos patitas y mueve la cola.
- 🖱️ Si mueves el mouse, levanta la patita izquierda y un mouse a su lado se mueve contigo (verde al hacer clic).
- 😊 En reposo mueve la cola, parpadea y a veces mira curioso.
- 💬 Salen teclitas voladoras con la letra que presionas.

<!-- Agrega aquí una captura o GIF: ![demo](docs/demo.gif) -->

## Instalación

### Opción A: ejecutable (sin instalar Python)
Descarga `PerritoWidget.exe` desde la sección [Releases](../../releases) y ábrelo.

### Opción B: desde el código
Requiere Python 3.9 o superior.

```bash
git clone https://github.com/TU_USUARIO/perrito-widget.git
cd perrito-widget
pip install -r requirements.txt
python perrito_widget.py
```

Para ejecutarlo sin ventana de terminal usa `pythonw perrito_widget.py`.

## Controles

| Acción | Resultado |
|---|---|
| Clic izquierdo + arrastrar | Mover al perrito |
| Rueda del mouse | Cambiar tamaño |
| Clic derecho | Menú (Siempre visible, Salir) |

## Iniciar con Windows

Presiona `Win + R`, escribe `shell:startup` y crea ahí un acceso directo a `PerritoWidget.exe`.

## Estructura

```
perrito_widget.py        programa principal
assets/frame_1..9.png    cuadros de animación (generados del sprite)
assets/source/           sprite sheet original 3x3
tools/make_assets.py     corta y alinea el sprite sheet en cuadros
```

Para cambiar al perrito, reemplaza `assets/source/labrador-sprite.png` (cuadrícula 3x3) y ejecuta:

```bash
pip install -r requirements-dev.txt
python tools/make_assets.py
```

Qué cuadro se usa en cada momento: 1 y 9 reposo, 5 parpadeo, 7 curioso, 2 y 8 patita izquierda, 3 patita derecha, 4 y 6 tecleo rápido.

## Crear el .exe tú mismo

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --add-data "assets;assets" --name PerritoWidget perrito_widget.py
```

El resultado queda en `dist/PerritoWidget.exe`. El flujo de GitHub Actions incluido lo compila solo al publicar una etiqueta `v*` (por ejemplo `v1.0.0`) y lo adjunta al Release.

## Privacidad

El programa escucha el teclado y los clics de forma global solo para animar al perrito. Muestra la tecla en pantalla, pero **no guarda ni envía nada**. Puedes revisarlo en `perrito_widget.py`.

## Problemas conocidos

- Si el perrito no reacciona dentro de programas abiertos como administrador, ejecútalo también como administrador.
- Algunos antivirus pueden marcar con falsos positivos los `.exe` creados con PyInstaller que escuchan el teclado. Si te preocupa, ejecútalo desde el código.

## Créditos

Arte del perrito: (agrega aquí el crédito del autor).

## Licencia

El código está bajo licencia [MIT](LICENSE). Las imágenes de `assets/` pueden tener condiciones distintas; revisa sus derechos antes de redistribuir.
