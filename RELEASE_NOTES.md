# CapturFácil 1.1.0

Publicación del 31 de octubre de 2026. Consolida las mejoras de las versiones 0.1.5–0.1.11 sobre la anterior release pública 0.1.4 beta.1. El funcionamiento de la aplicación es el de 0.1.11; esta publicación actualiza la versión y reúne la documentación para nuevos usuarios.

## Cambios principales

- Captura rápida de pantalla en X11 con scrot y archivo temporal BMP; el resultado final sigue siendo PNG. GNOME continúa como alternativa y para área/ventana.
- Opción Modo compatible (GNOME) ante problemas con la imagen.
- Movimiento y ajuste de rectángulos, óvalos y trazos a mano alzada, con tiradores visibles. Flechas y líneas ajustables desde sus dos extremos.
- Cambio de color y tamaño del texto ya colocado; cambios de estilo y movimientos incluidos en deshacer/rehacer.
- Corrección de la captura incompleta que apareció durante las pruebas de una vía rápida anterior.
- Restauración de la ventana y solicitud de foco renovada al volver a activar la aplicación en X11.
- Devolución explícita de Impr Pant a GNOME, también ante copias de configuración incompletas.
- Registro de los PNG guardados en Recientes sin necesidad de abrirlos antes, respetando la preferencia de historial del escritorio.
- Indicadores de tiempos de preparación, captura, carga y visualización.

## Instalación y actualización

Descarga `capturfacil_1.1.0_all.deb` y, desde su carpeta, ejecuta:

```bash
sudo apt install ./capturfacil_1.1.0_all.deb
```

APT instala las dependencias, incluida scrot. Guarda el trabajo y cierra la ventana antes de actualizar; instala encima de la versión anterior. No hace falta desinstalar. Comprueba la versión con `capturfacil --version`.

Abre CapturFácil desde el menú y pulsa Usar CapturFácil con Impr Pant si deseas asignarle la tecla. Para volver al capturador nativo, utiliza Devolver Impr Pant a GNOME o Restablecer Impr Pant de GNOME en la pantalla inicial.

Listo · guardar exporta a la carpeta de imágenes del escritorio, dentro de Capturas de pantalla, registra la imagen en Recientes y oculta la ventana. Copiar no guarda un archivo.

La [guía completa](README.md) explica dependencias, anotaciones, atajos, desinstalación, modo compatible y solución de problemas.

## Validación y límites

55 pruebas automatizadas. Pruebas manuales del flujo de captura, anotaciones, guardado, Recientes y devolución a GNOME en Linux Mint 22.1 con GNOME sobre X11, varios monitores y escalado al 200 %.

En una medición real, Pantalla actual pasó de unos cinco segundos a 0,73 segundos desde la elección del modo hasta mostrar la imagen. El resultado depende del equipo y del modo; Ventana mantiene una espera de tres segundos.

Wayland y otros escritorios no están validados. Queda pendiente ampliar la validación del portapapeles y de la restauración automática durante la desinstalación. El texto se mueve y cambia de estilo, pero su contenido aún no se puede reescribir. La exportación es un PNG aplanado, no un proyecto editable. Véase [PENDIENTES.md](PENDIENTES.md).
