# Plan&Go base

## Tutorial de ejecución

### Levantar la Aplicación

```bash

docker build -t plan-go .
docker run --env-file .env -p 8000:8000 plan-go

```

La aplicación se instanciará en http://localhost:8000