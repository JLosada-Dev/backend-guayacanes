.PHONY: up down dev reset logs shell migrate data

# Levantar DB + Redis en background
up:
	docker compose up -d

# Bajar contenedores
down:
	docker compose down

# Servidor de desarrollo (levanta Docker y espera que PostgreSQL esté listo)
dev: up
	@echo "Esperando PostgreSQL..."
	@until docker exec guyacanes_db pg_isready -q; do sleep 1; done
	uv run python manage.py runserver 0.0.0.0:8000

# Migraciones
migrate:
	uv run python manage.py migrate

# Cargar datos iniciales (fixtures + geodatos)
data:
	uv run python manage.py loaddata fixtures/core_services.json
	uv run python manage.py loaddata fixtures/core_aspects.json
	uv run python manage.py load_communes
	uv run python manage.py load_sweeping

# Setup completo desde cero
reset: migrate data
	@echo "Base de datos lista."

# Logs de Docker
logs:
	docker compose logs -f

# Shell de Django
shell:
	uv run python manage.py shell
