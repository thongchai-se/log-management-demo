.PHONY: up down build logs seed test certs health reset-index

up: certs
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f --tail=100

certs:
	@mkdir -p deploy/nginx/certs
	@if [ ! -f deploy/nginx/certs/server.crt ]; then \
		bash deploy/nginx/generate-certs.sh; \
	else \
		echo "TLS certs already exist"; \
	fi

seed:
	python sample/post_logs.py
	python sample/seed_alerts.py
	python sample/send_syslog.py

test:
	cd backend && python -m pytest ../tests -q

health:
	curl -sk https://localhost/health || curl -s http://127.0.0.1:8000/health

reset-index:
	curl -s -X DELETE http://127.0.0.1:9200/logs || true
	@echo "Index deleted. Restart backend or POST /api/admin/index/ensure"
