# CapturFácil 0.1.4 beta.1

Versión de pruebas en desarrollo, no estable. Publicada el 30 de octubre de 2026. Conserva el instalador 0.1.4 probado por el usuario; esta publicación no introduce correcciones adicionales.

## Mejoras comprobadas

- El texto ya colocado se puede mover y cambiar de color y tamaño.
- Captura ampliada, anotaciones, guardado automático y fondo transparente incorporados en esta serie.

## Problemas conocidos y siguientes pasos

- **Formas:** el usuario no ve los tiradores para ajustar óvalos/círculos existentes. Aunque hay código y pruebas para selección y redimensionado, la interacción visual no está validada. Revisar también rectángulos; no dar esta mejora por resuelta.
- **Primera apertura:** sigue siendo lenta, aunque se aprecia cierta mejora. Medir el recorrido real desde Impr Pant hasta la ventana visible.
- **Segunda apertura:** puede quedar detrás de otras ventanas y mostrar un aviso de que está preparada, obligando a pulsar para traerla al frente. Corregir la activación y el foco de GNOME.
- Pendientes de validación completa: portapapeles, restauración del atajo al desinstalar, otros escritorios y Wayland.

## Validación e instalación

33 pruebas automatizadas superadas. No sustituyen la comprobación visual en el escritorio. Entorno probado por el usuario: Linux Mint / Ubuntu, GNOME sobre X11.

Descargar capturfacil_0.1.4_all.deb, cerrar la ventana de CapturFácil e instalar encima de la anterior. No es necesario desinstalar primero. El paquete sigue identificándose como 0.1.4; v0.1.4-beta.1 identifica esta publicación de prueba.
