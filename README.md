# CapturFácil 1.1.0

Capturas de pantalla y anotaciones sencillas para Linux con GNOME. Elige qué capturar, añade los retoques que necesites y pulsa **Listo · guardar**. La imagen se guarda en PNG y la ventana se oculta hasta la siguiente captura.

Desarrollada por Paco Estrada con asistencia de IA para simplificar un flujo de trabajo cotidiano. Python 3, GTK 3 y Cairo, sin Electron ni servicios de red.

**[Descargar en GitHub](https://github.com/pacoestrada/capturfacil/releases/tag/v1.1.0)** · **[Descargar en GitLab](https://gitlab.com/PacoEstrada/capturfacil/-/releases/v1.1.0)** · [Cambios](RELEASE_NOTES.md) · [Pendientes](PENDIENTES.md)

## Requisitos y compatibilidad

El entorno probado es **Linux Mint 22.1, base Ubuntu 24.04, con GNOME y sesión X11**, incluidos varios monitores y escalado al 200 %. El paquete Debian es de arquitectura `all`: contiene código Python, pero necesita las bibliotecas y herramientas del sistema.

Wayland, KDE Plasma, Cinnamon y otras distribuciones no están validados. La gestión automática de Impr Pant necesita los ajustes de GNOME. Admitir paquetes `.deb` no garantiza por sí solo la compatibilidad.

El paquete declara estas dependencias; APT las instala desde los repositorios de la distribución:

| Paquetes | Función |
| --- | --- |
| `python3` | Ejecución de la aplicación |
| `python3-gi`, `python3-gi-cairo`, `python3-cairo` | Integración con GTK y dibujo |
| `gir1.2-gtk-3.0`, `gir1.2-pango-1.0` | Interfaz y texto |
| `scrot` | Captura rápida de pantalla en X11 |
| `gnome-screenshot` | Captura de área, ventana y modo compatible |
| `util-linux`, `libglib2.0-bin` | Integración con la sesión y gestión del paquete |

`gnome-shell` figura como recomendado. No es necesario instalar módulos con pip.

## Instalación

Descarga **capturfacil_1.1.0_all.deb** de los archivos adjuntos de la release. No uses los instaladores antiguos que puedan seguir en el historial del repositorio.

Desde la carpeta donde lo hayas descargado:

```bash
sudo apt install ./capturfacil_1.1.0_all.deb
```

También puedes abrir el archivo con el instalador gráfico de paquetes. Completa la instalación; descargarlo no actualiza la app. Si faltan dependencias, utiliza el comando anterior para que APT las resuelva. Ejecuta CapturFácil como usuario normal, nunca con sudo.

Comprueba la versión instalada:

```bash
capturfacil --version
```

### Actualizar desde una versión anterior

Guarda el trabajo pendiente y cierra la ventana. Instala el nuevo paquete encima, sin desinstalar primero. La actualización conserva la asignación de Impr Pant y las capturas guardadas. La instancia oculta detecta la actualización y se recarga; deja unos segundos para que termine. Si sigue apareciendo una versión antigua, ejecuta `capturfacil --quit` y vuelve a abrirla desde el menú.

## Primer uso

1. Abre **CapturFácil** desde el menú de aplicaciones.
2. Para usar la tecla, pulsa **Usar CapturFácil con Impr Pant**. La instalación por sí sola no sustituye el atajo. Puedes seguir abriendo la app desde el menú.
3. Pulsa Impr Pant y elige **Pantalla actual**, **Todas las pantallas**, **Ventana** o **Área**. Pantalla actual corresponde al monitor donde está la aplicación. Para Ventana hay tres segundos para activar la ventana deseada; para Área, arrastra la selección o pulsa Esc para cancelar.
4. Pulsa **Retoques** para anotar, o guarda directamente.
5. Pulsa **Listo · guardar**. La ventana se oculta, libera la imagen y queda preparada para otra captura. La siguiente pulsación de Impr Pant vuelve a mostrar el selector.

Cuando el atajo está activado, la app puede permanecer en segundo plano y precargarse al iniciar sesión. Para terminar el proceso por completo, utiliza `capturfacil --quit`.

## Anotaciones y navegación

- Flechas, líneas, líneas de puntos, rectángulos, óvalos, texto y dibujo a mano alzada.
- Selecciona una anotación para moverla y cambiar su color o grosor. El texto permite cambiar su tamaño y color después de colocarlo.
- Rectángulos, óvalos y trazos a mano alzada tienen tiradores para ajustar sus dimensiones. Flechas y líneas tienen un tirador en cada extremo. Los tiradores no se exportan.
- Deshacer y rehacer incluyen movimientos y cambios de estilo. Esc cancela un arrastre en curso.
- El editor se abre maximizado. Puedes ajustar la imagen a la ventana, verla al 100 % o cambiar el zoom. La exportación conserva la resolución de la captura.
- El selector y los márgenes pueden ser transparentes si el escritorio lo permite. La captura es una imagen fija, no una vista en directo del escritorio.

| Atajo | Acción |
| --- | --- |
| Ctrl+Z | Deshacer |
| Ctrl+Y / Ctrl+Mayús+Z | Rehacer |
| Ctrl+S | Guardar y ocultar la ventana |
| Ctrl+C | Copiar la imagen anotada |
| Ctrl+rueda | Cambiar zoom |
| Botón central y arrastrar | Desplazar la vista |
| F11 | Alternar pantalla completa |

El contenido de un texto ya colocado todavía no se puede reescribir. El PNG exportado queda aplanado; no se guarda un proyecto con anotaciones editables para abrir más tarde.

## Dónde se guardan las capturas

En la carpeta de imágenes configurada en el escritorio, dentro de **Capturas de pantalla**. Por ejemplo, `~/Imágenes/Capturas de pantalla`. El nombre incluye fecha, hora y microsegundos, como `Captura_2026-10-31_14-00-00_123456.png`.

**Abrir carpeta** lleva a la ubicación exacta. Las capturas nuevas se registran en **Recientes** al guardarlas, sin abrirlas antes, siempre que el historial de archivos esté habilitado. No se añaden automáticamente capturas antiguas.

**Copiar** solo lleva la imagen al portapapeles; no equivale a guardarla. Un guardado repetido sin cambios no duplica el archivo. Si se modifican las anotaciones y se guarda de nuevo, se conserva también la imagen anterior. Si falla la exportación, la app muestra un error y conserva el trabajo.

## Volver al capturador de GNOME

En la pantalla inicial pulsa **Devolver Impr Pant a GNOME** o **Restablecer Impr Pant de GNOME**. Se retira la asignación de CapturFácil y se activa el atajo de captura de GNOME. No hace falta desinstalar y puedes seguir usando CapturFácil desde el menú.

La aplicación guarda la configuración anterior antes de hacerse cargo de Impr Pant. Si detecta que esa tecla pertenece a otro atajo personalizado, avisa en lugar de sustituirlo. La configuración se aplica al usuario actual, no a todas las cuentas del equipo.

### Desinstalar

Se recomienda devolver primero Impr Pant a GNOME desde la app y después ejecutar:

```bash
sudo apt remove capturfacil
```

El paquete también intenta restaurar la configuración anterior durante la desinstalación en las sesiones activas. Para sesiones cerradas conserva un recuperador por usuario que actúa en el siguiente inicio de sesión y se retira después. Se respetan las reasignaciones posteriores a otras aplicaciones. Este recorrido automático de desinstalación todavía necesita más pruebas en escritorios reales; la devolución desde el botón sí está comprobada en el entorno indicado.

Las imágenes guardadas no se eliminan al desinstalar.

## Rendimiento y resolución de problemas

En X11, Pantalla actual y Todas las pantallas utilizan scrot y un archivo temporal BMP para reducir el tiempo de codificación. La exportación final sigue siendo PNG. Área y Ventana utilizan gnome-screenshot; también se mantiene como alternativa si el método rápido falla.

Si una captura aparece incompleta o incorrecta, activa **Modo compatible (GNOME)** antes de capturar. Esta opción se conserva durante la instancia actual de la app. Wayland utiliza la vía compatible, pero no está validado.

La barra inferior muestra tiempos de preparación, captura, carga y visualización. Se miden desde que se elige el tipo de captura, no desde la pulsación física de Impr Pant. Ventana incluye su espera de tres segundos y Área incluye el tiempo empleado en seleccionar. En una prueba real de Pantalla actual se pasó de unos cinco segundos a 0,73 segundos; es una medición de un equipo, no una garantía universal.

Si un archivo no aparece en Recientes, comprueba la versión instalada, guarda una captura nueva y verifica que el historial del escritorio esté habilitado. Si no sabes dónde se guardó, usa Abrir carpeta. Para informar de un problema, indica versión de CapturFácil, distribución, escritorio, X11 o Wayland, monitores/escalado, tipo de captura y tiempos mostrados. Evita adjuntar imágenes con datos privados.

## Código fuente y pruebas

Repositorios: [GitHub](https://github.com/pacoestrada/capturfacil) y [GitLab](https://gitlab.com/PacoEstrada/capturfacil).

El paquete instala el código en `/usr/share/capturfacil` e incluye fuentes, pruebas y constructor en `/usr/share/doc/capturfacil/source.tar.gz`.

Con las dependencias instaladas, desde el directorio del proyecto:

```bash
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 build.py
```

La construcción requiere dpkg-deb (paquete dpkg) y genera el instalador en dist/. Las pruebas automatizadas aíslan los ajustes de GNOME. Las pruebas gráficas requieren una sesión de escritorio accesible.

La versión 1.1.0 consolida el comportamiento probado de 0.1.11. Consulta [las notas de publicación](RELEASE_NOTES.md) y [los pendientes](PENDIENTES.md). La aplicación no envía capturas ni datos a servidores.
