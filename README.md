# CapturFácil 0.1.4 · beta

> **Beta en desarrollo.** El texto se puede mover y cambiar de color/tamaño. Siguen abiertos los problemas de tiradores en formas, primera apertura lenta y reapertura detrás de otras ventanas. Consulta [PENDIENTES.md](PENDIENTES.md). No es una versión estable.

Capturas y anotaciones sencillas para GNOME sobre X11. Aplicación en desarrollo. Versión 0.1.4 de prueba. La versión anterior, 0.1.2, fue probada por su usuario en GNOME sobre X11.

## Instalación y primer uso

Abre `capturfacil_0.1.4_all.deb` con el instalador de paquetes e instala sus dependencias. También puedes ejecutar `sudo apt install ./capturfacil_0.1.4_all.deb` desde la carpeta en la que lo hayas descargado.

Abre **CapturFácil** desde el menú de aplicaciones y pulsa **Usar CapturFácil con Impr Pant** una sola vez. La activación se realiza dentro de tu sesión, sin permisos de administrador. No cambia el atajo hasta que pulses ese botón.

1. Pulsa Impr Pant y elige Pantalla actual, Todas las pantallas, Ventana o Área. Pantalla actual captura el monitor donde está abierta CapturFácil.
2. En modo ventana, haz clic en la ventana deseada durante los tres segundos de espera. En modo área, selecciona arrastrando; Esc cancela.
3. Pulsa **Retoques** y elige flecha, línea, puntos, círculo/óvalo, rectángulo, texto o mano alzada.
4. Arrastra sobre la imagen para dibujar. Para texto, haz clic donde quieras colocarlo y escribe.
5. Pulsa **Listo · guardar**. La ventana se oculta después de guardar y queda preparada en segundo plano, liberando la captura de memoria. El PNG se guarda en la carpeta de imágenes configurada en tu escritorio, dentro de **Capturas de pantalla**, con fecha y hora. La imagen conserva su resolución original.

**Copiar** lleva la imagen anotada al portapapeles. Copiar no equivale a guardar. **Abrir carpeta** muestra los archivos. Si cierras o inicias otra captura sin guardar, puedes guardar, descartar o cancelar.

Los retoques usan color y grosor comunes. El grosor y el tamaño del texto se aplican al tamaño visible mientras dibujas, para que las anotaciones no queden diminutas cuando la captura se muestra reducida. El texto tiene su propio tamaño. Ctrl+Z deshace, Ctrl+Y o Ctrl+Mayús+Z rehace, Ctrl+S guarda y Ctrl+C copia. Un segundo guardado sin cambios no crea un duplicado; si cambias las anotaciones, se guarda otro archivo para conservar el anterior.

## Recuperar Impr Pant y desinstalar

Para volver a GNOME sin desinstalar, en la pantalla inicial pulsa **Devolver Impr Pant a GNOME**. Se restaura la configuración previa, que podría ser distinta de la configuración de fábrica.

Desinstala desde el gestor de software o con `sudo apt remove capturfacil`. El paquete intenta recuperar el atajo en las sesiones de usuario activas. Para usuarios con la sesión cerrada o si no puede acceder a su bus de sesión, un pequeño recuperador guardado en la configuración del usuario se ejecuta en el siguiente inicio de sesión. Después de recuperar el atajo elimina su propia copia y su entrada de inicio automático.

Una actualización del paquete no devuelve el atajo a GNOME. Los cambios posteriores del usuario se respetan: si has reasignado el atajo a otra aplicación, la desinstalación no fuerza el valor antiguo.

Las capturas guardadas nunca se eliminan al desinstalar. La aplicación no envía imágenes ni datos a ningún servidor.

## Alcance de esta versión

Pensada para Linux Mint 22.x / Ubuntu 24.04, GNOME y X11, con gnome-screenshot. Otros escritorios y Wayland no están validados. Todas las pantallas incluye el escritorio conjunto. Pantalla actual recorta el monitor donde está la aplicación; Área permite escoger una parte.

Se puede mover el texto ya colocado, con Texto o Seleccionar / mover, y deshacer o rehacer tanto su creación como sus movimientos. El código incorpora movimiento y ajuste de rectángulos y óvalos, pero el usuario no ve los tiradores: esta función sigue pendiente de corrección y validación visual. Selecciona texto para cambiar su color o tamaño en la barra lateral. El contenido escrito todavía no se puede editar. La previsualización se ajusta a la ventana. Puedes ampliar con +, reducir con −, volver a Ajustar o usar 100 %. Ctrl+rueda cambia el zoom. Las barras permiten recorrer la imagen; también puedes arrastrarla con el botón central. F11 alterna la pantalla completa. El editor se abre maximizado.

Validación realizada: pruebas automatizadas de renderizado a resolución original, PNG, activación/restauración del atajo con ajustes aislados, respeto de cambios posteriores y recuperación ante errores. Se comprueba también la estructura del paquete y la sintaxis del código. El usuario ha probado capturas y anotaciones y confirma que la versión 0.1.2 resulta más práctica y arranca antes. Sigue pendiente la comprobación completa del portapapeles y del ciclo de desinstalación. Las pruebas automatizadas usan ajustes aislados; no sustituyen la validación del escritorio.

## Código fuente

Python 3, GTK 3 y Cairo. No utiliza Electron ni servicios de red.

Código instalado en `/usr/share/capturfacil`. Fuente completo y procedimiento de construcción en `/usr/share/doc/capturfacil/source.tar.gz`.

Para reconstruir: extrae el archivo fuente y ejecuta `python3 build.py`. Se necesita `dpkg-deb`. Para las pruebas: `python3 -m unittest discover -s tests -v`. `tests/gui_smoke.py` requiere una sesión gráfica accesible y guarda imágenes de prueba en `/tmp/capturfacil/qa`; no cambia los atajos ni el portapapeles del usuario.

## Apertura rápida

Después del primer arranque, Impr Pant pide a la instancia que ya está abierta en segundo plano que muestre la ventana, sin volver a cargar el editor. Al iniciar una sesión GNOME se precarga de forma oculta solo si tienes activado su atajo. La instalación intenta precargar la aplicación en las sesiones activas que ya tienen el atajo habilitado, mediante D-Bus y sin abrir ventanas. Si no puede hacerlo, el primer arranque será en frío. No se ha medido el tiempo real de apertura en el escritorio del usuario.

Listo · guardar (también Ctrl+S) guarda y oculta la ventana. La siguiente pulsación de Impr Pant abre el selector para una nueva captura. El archivo recién guardado tiene fecha de modificación actual; en el explorador, ordenar por fecha de modificación descendente lo muestra primero. La aplicación no cambia el orden de las carpetas de tu explorador.

Para terminar completamente el proceso, ejecuta `capturfacil --quit`. Una instancia oculta detecta una actualización y se sustituye por la nueva versión en segundo plano, si el atajo sigue activo. Al desinstalar, sale.

## Transparencia y movimiento

- Fondo transparente real en el selector y en los márgenes de la captura, cuando GNOME tiene composición y un visual RGBA. Las herramientas y la captura permanecen opacas. No se modifica la opacidad del PNG ni se dibuja sobre otras aplicaciones. Si el escritorio no admite transparencia, se usa un fondo normal.
- Para mover un texto, activa Retoques y elige **Seleccionar / mover**, pulsa sobre el texto y arrástralo. También puedes arrastrar un texto existente con la herramienta Texto. Un recuadro indica la selección; no se guarda en la imagen.
- Ctrl+Z deshace un movimiento completo; Ctrl+Y lo rehace. Esc durante el arrastre cancela el movimiento. El texto se mantiene dentro de los límites de la captura.

La transparencia real y la interacción visual de esta actualización requieren comprobación en la sesión de escritorio del usuario. El entorno de construcción no dispone de acceso al servidor gráfico.

## Novedades de 0.1.4

Seleccionar / mover permite arrastrar textos. La selección y los tiradores de las formas están implementados, pero no funcionan de manera validada en el escritorio del usuario; siguen en revisión. El interior también permite seleccionar. Texto selecciona solamente texto y crea uno nuevo al pulsar fuera de un texto existente.

Con texto seleccionado, Color y Texto cambian la anotación existente. Con una forma seleccionada puedes cambiar Color y Grosor. Las modificaciones se guardan en el PNG y se pueden deshacer y rehacer. Esc durante un arrastre lo cancela. Para dibujar otra anotación, elige su herramienta.

La precarga de sesión ya no espera cinco segundos ni se limita al identificador GNOME. Solo permanece activa cuando el atajo está habilitado. Al actualizar, el instalador espera seis segundos para que una versión antigua oculta salga y solicita la precarga a D-Bus. No cierra ventanas con trabajo abierto ni modifica el atajo. Cierra la ventana antes de actualizar para que este recorrido pueda completarse.
