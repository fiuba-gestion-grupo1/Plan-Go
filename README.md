# Plan & Go

## Tutorial de ejecución

La aplicación se instanciará en http://localhost:8000.

**ATENCION**

Es necesario que previa a la ejecucion de la aplicacion se cree un archivo ```.env``` en la raiz del directorio. Adjunto en el repositorio hay un archivo ```.env.example``` con el formato que debe tener el archivo ```.env```

Esta es una medida de seguridad ya que en el archivo ```.env``` se almacena el JWT Token propio de cada usuario. No debe ser compartido.

### Construir la imagen de la Aplicación

```bash

make build

```

### Levantar la Aplicación

```bash

make up

```

### Bajar la Aplicación

```bash

make down

```

### Ver los logs de la Aplicación

```bash

make logs

```

### Reiniciar la Aplicación

```bash

make restart

```

### Ejecutar los tests unitarios

La ejecucion de los tests se realiza en un contenedor de docker que contiene todas las dependencias y requerimientos necesarios instalados para correr los tests correctamente.

Ejecutar el comando:

```bash

make test

```

Para levantar el contenedor y correr los tests. Automaticamente terminada la ejecucion de los tests, el conetenedor se elimina automaticamente para limpiar los recursos.
