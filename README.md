# 🐶 Perrito Widget

Un perrito de escritorio para Windows 11 que teclea y mueve el mouse contigo.

- 👀 Sus ojos siguen el cursor y parpadea.
- 🖱️ Una patita mueve el mouse cuando tú lo mueves; se pone verde al hacer clic.
- ⌨️ La otra patita teclea y salen teclitas voladoras con la letra que presionas.
- 🐕 Mueve la cola y las orejas más rápido cuando escribes.

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

## Crear el .exe tú mismo

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name PerritoWidget perrito_widget.py
```

El resultado queda en `dist/PerritoWidget.exe`. Este repositorio también incluye un flujo de GitHub Actions que lo compila automáticamente al publicar una etiqueta `v*` (por ejemplo `v1.0.0`) y lo adjunta al Release.

## Privacidad

El programa escucha el teclado y los clics de forma global solo para animar al perrito. Muestra la tecla en pantalla, pero **no guarda ni envía nada**. Puedes revisarlo en `perrito_widget.py`.

## Problemas conocidos

- Si el perrito no reacciona dentro de programas abiertos como administrador, ejecútalo también como administrador.
- Algunos antivirus pueden marcar con falsos positivos los `.exe` creados con PyInstaller que escuchan el teclado. Si te preocupa, ejecútalo desde el código.

## Licencia

[MIT](LICENSE)
