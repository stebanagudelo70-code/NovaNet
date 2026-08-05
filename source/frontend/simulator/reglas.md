# Simulador de Red ISP — Descripcion del Proyecto

## Que es

Una aplicacion web interactiva que simula una pequena red de servicio de un proveedor de internet, compuesta por 10 routers domésticos. Permite visualizar, gestionar y simular fallas en la red en tiempo real.

## Routers

La red esta conformada por 10 routers con los siguientes nombres y configuraciones:

| Router | IP |
|---|---|
| Router-Alpha | 192.168.1.1 |
| Router-Bravo | 192.168.2.1 |
| Router-Charlie | 192.168.3.1 |
| Router-Delta | 192.168.4.1 |
| Router-Echo | 192.168.5.1 |
| Router-Foxtrot | 192.168.6.1 |
| Router-Golf | 192.168.7.1 |
| Router-Hotel | 192.168.8.1 |
| Router-India | 192.168.9.1 |
| Router-Juliet | 192.168.10.1 |

## Estados de los routers

Cada router puede estar en uno de tres estados:

- **Verde (Funcional):** El router opera correctamente, los clientes tienen conexion.
- **Naranja (Con falla):** El router presenta una falla menor que puede afectar la calidad del servicio pero no corta la conexion completamente.
- **Rojo (Requiere tecnico):** El router tiene una falla critica que requiere intervencion de un tecnico para ser reparada.

## Funcionalidades

### Cambio manual de estados
El usuario tecnico puede cambiar manualmente el estado de cualquier router desde la interfaz, seleccionando el estado deseado con un clic.

### Cambio automatico de estados
La simulacion genera fallas automaticas cada 30 minutos en un router aleatorio de la red que se encuentre funcionando. El tipo de falla se determina de forma probabilistica: 40% de probabilidad de ser un fallo critico (rojo) y 60% de probabilidad de ser una falla menor (naranja).

### Alertas visuales
Cuando un router pasa a estado rojo, se activan las siguientes alertas:
- Una notificacion emergente (toast) en la esquina superior derecha de la pantalla.
- Una tarjeta de alerta en el panel lateral derecho con el nombre del router, su direccion IP y el tiempo que lleva en estado critico.
- El router en estado rojo muestra un efecto de pulso visual con borde rojo parpadeante.

### Historial de eventos
Se lleva un registro cronologico de todos los cambios de estado que ocurren en la red. Cada registro incluye:
- Hora del cambio.
- Nombre del router afectado.
- Estado anterior y nuevo estado.
- Razon del cambio (manual, automatica o reparacion).

El historial se puede filtrar por router especifico o ver todos los eventos juntos.

### Panel de estadisticas
Muestra metricas en tiempo real de la condicion de la red:
- **Operativos:** Cantidad y porcentaje de routers en estado verde.
- **Con falla:** Cantidad y porcentaje de routers en estado naranja.
- **Requieren tecnico:** Cantidad y porcentaje de routers en estado rojo.
- **Disponibilidad:** Porcentaje general de la red operativa y tiempo promedio en falla de los routers afectados.
- **Barras de progreso:** Representacion visual de la distribucion porcentual de cada estado.

### Roles de usuario

#### Cliente
- Solo puede ver el estado de su propio router asignado (Router-Alpha).
- Visualiza si su router esta operativo o con problemas.
- Puede enviar un reporte de falla (simulado) cuando su router no esta en estado verde.
- No tiene acceso a controles de simulacion, estadisticas de red completa ni historial de todos los routers.

#### Tecnico
- Tiene acceso completo a la red: ve los 10 routers con su informacion detallada.
- Puede cambiar manualmente el estado de cualquier router.
- Tiene acceso a botones de reparacion rapida para routers en estado rojo.
- Puede activar simulaciones de fallas para pruebas.
- Ve el panel completo de estadisticas, barras de progreso y historial de eventos.
- Puede restablecer todos los routers a estado funcional con un solo boton.

## Simulacion rapida (modo prueba)

Para fines de demostracion, se incluyen botones que permiten:
- **Simular falla ahora:** Genera una falla inmediata en un router aleatorio.
- **Simular 3 fallas:** Genera 3 fallos consecutivos con medio segundo de diferencia entre cada uno.
- **Restablecer todo:** Devuelve todos los routers a estado verde.
- La primera falla automatica ocurre a los 30 segundos de iniciar sesion como tecnico, ademas del intervalo regular de 30 minutos.

## Interfaz

- Tema oscuro con diseno responsive.
- Tarjetas de router con indicador visual de estado, barras de progreso y acciones.
- Panel lateral con pestanas de Alertas e Historial.
- Reloj en tiempo real en el header.
- Notificaciones toast que aparecen y se desvanecen automaticamente.
- Layout en dos columnas: contenido principal a la izquierda, panel lateral a la derecha.
