SHELL := /bin/sh

FRONTEND_PORT ?= 5173
BACKEND_PORT ?= 8000
STATE_DIR ?= .steadwork
LOG_DIR ?= $(STATE_DIR)/logs
PLAYWRIGHT_BROWSERS_PATH ?= $(CURDIR)/e2e/.cache/ms-playwright
IMAGE_REF ?=
IMAGE_TAG ?=

.PHONY: dev run frontend backend install setup stop cleanup e2e test test-fast \
	e2e-install test-setup test-frontend test-backend deploy deploy-prod apply-dev destroy-dev destroy-prod destroy-bootstrap

FRONTEND_TEST_COMMAND ?= npm test
BACKEND_TEST_COMMAND ?= cd backend && uv run pytest -q

dev:
	@set -eu; \
	mkdir -p "$(LOG_DIR)"; \
	rm -f "$(STATE_DIR)/frontend.status" "$(STATE_DIR)/backend.status"; \
	command -v setsid >/dev/null 2>&1 || { printf '%s\n' "make dev requires setsid to isolate service process groups" >&2; exit 1; }; \
	start_service() { \
		name=$$1; shift; \
		STEADWORK_STATUS_FILE="$(STATE_DIR)/$$name.status" setsid sh -c ' \
			status=0; \
			"$$@" || status=$$?; \
			printf "%s\n" "$$status" >"$$STEADWORK_STATUS_FILE"; \
			exit "$$status" \
		' service "$$@" >"$(LOG_DIR)/$$name.log" 2>&1 & \
		printf '%s\n' "$$!"; \
	}; \
	frontend_pid=$$(start_service frontend sh -c 'cd frontend && exec npm run dev -- --host 127.0.0.1 --port "$(FRONTEND_PORT)"'); \
	backend_pid=$$(start_service backend sh -c 'cd backend && exec uv run python manage.py runserver "127.0.0.1:$(BACKEND_PORT)"'); \
	printf '%s\n' "$$frontend_pid" >"$(STATE_DIR)/frontend.pid"; \
	printf '%s\n' "$$backend_pid" >"$(STATE_DIR)/backend.pid"; \
	stop_group() { kill -TERM "-$$1" 2>/dev/null || true; }; \
	cleanup() { stop_group "$$frontend_pid"; stop_group "$$backend_pid"; wait "$$frontend_pid" "$$backend_pid" 2>/dev/null || true; rm -f "$(STATE_DIR)"/frontend.pid "$(STATE_DIR)"/backend.pid; }; \
	trap cleanup EXIT; \
	trap 'exit 130' INT TERM; \
	ready=0; attempt=0; \
	while [ "$$attempt" -lt 60 ]; do \
		if [ -f "$(STATE_DIR)/frontend.status" ] || [ -f "$(STATE_DIR)/backend.status" ]; then break; fi; \
		if curl -fsS "http://127.0.0.1:$(FRONTEND_PORT)/" >/dev/null 2>&1 && curl -fsS "http://127.0.0.1:$(BACKEND_PORT)/api/health/" >/dev/null 2>&1; then ready=1; break; fi; \
		attempt=$$((attempt + 1)); sleep 1; \
	done; \
	if [ "$$ready" -eq 1 ]; then \
		printf '%s\n' "Steadwork is running:" "  App:     http://127.0.0.1:$(FRONTEND_PORT)" "  API:     http://127.0.0.1:$(BACKEND_PORT)/api/" "  Logs:    $(LOG_DIR)/frontend.log and $(LOG_DIR)/backend.log"; \
		tail -f "$(LOG_DIR)/frontend.log" "$(LOG_DIR)/backend.log"; \
	fi; \
	printf '%s\n' "Services did not become ready within 60 seconds; startup logs follow:" >&2; \
	cat "$(LOG_DIR)/frontend.log" "$(LOG_DIR)/backend.log" >&2; \
	if [ "$$ready" -ne 1 ]; then exit 1; fi; \
	status=0; \
	if [ -f "$(STATE_DIR)/frontend.status" ]; then \
		frontend_status=$$(cat "$(STATE_DIR)/frontend.status"); \
		[ "$$frontend_status" -eq 0 ] || status=$$frontend_status; \
		printf '%s\n' "Frontend exited with status $$frontend_status; see $(LOG_DIR)/frontend.log" >&2; \
	fi; \
	if [ -f "$(STATE_DIR)/backend.status" ]; then \
		backend_status=$$(cat "$(STATE_DIR)/backend.status"); \
		[ "$$backend_status" -eq 0 ] || status=$$backend_status; \
		printf '%s\n' "Backend exited with status $$backend_status; see $(LOG_DIR)/backend.log" >&2; \
	fi; \
	exit "$$status"

frontend:
	cd frontend && npm run dev -- --port "$(FRONTEND_PORT)"

backend:
	cd backend && uv run python manage.py runserver "127.0.0.1:$(BACKEND_PORT)"

install:
	npm --prefix frontend ci
	cd backend && uv sync

setup: install

# Promotion runs the protected GitHub Actions workflow. Blank IMAGE_TAG uses
# the image last deployed successfully to development; set it for a rollback.
deploy:
	@test "$(ENV)" = "prod" || { printf '%s\n' 'Usage: make deploy ENV=prod [IMAGE_TAG=YYYYMMDD-HHMMSS-shortsha]' >&2; exit 2; }
	@command -v gh >/dev/null 2>&1 || { printf '%s\n' 'GitHub CLI (gh) is required; install it and run gh auth login.' >&2; exit 2; }
	gh workflow run deploy-prod.yml --ref main -f image_tag="$(IMAGE_TAG)"

deploy-prod:
	@$(MAKE) --no-print-directory deploy ENV=prod IMAGE_TAG="$(IMAGE_TAG)"

apply-dev:
	@test -n "$(TF_CLOUD_ORGANIZATION)" || { printf '%s\n' 'Set TF_CLOUD_ORGANIZATION to your HCP Terraform organization.' >&2; exit 2; }
	@test -n "$(IMAGE_REF)" || { printf '%s\n' 'IMAGE_REF must be an immutable image reference, e.g. ghcr.io/owner/repo@sha256:...'; exit 2; }
	@set -eu; image_url=$${IMAGE_REF%@*}; image_digest=$${IMAGE_REF##*@}; \
	terraform -chdir=deployment/terraform/bootstrap init -backend-config="organization=$(TF_CLOUD_ORGANIZATION)" -backend-config="workspaces.name=steadwork-bootstrap"; \
	terraform -chdir=deployment/terraform/bootstrap apply -var="project_name=steadwork"; \
	terraform -chdir=deployment/terraform/dev init -backend-config="organization=$(TF_CLOUD_ORGANIZATION)" -backend-config="workspaces.name=steadwork-dev"; \
	terraform -chdir=deployment/terraform/dev apply -var="terraform_organization=$(TF_CLOUD_ORGANIZATION)" -var="image_url=$$image_url" -var="image_digest=$$image_digest"

destroy-dev:
	@test -n "$(TF_CLOUD_ORGANIZATION)" || { printf '%s\n' 'Set TF_CLOUD_ORGANIZATION to your HCP Terraform organization.' >&2; exit 2; }
	terraform -chdir=deployment/terraform/dev init -backend-config="organization=$(TF_CLOUD_ORGANIZATION)" -backend-config="workspaces.name=steadwork-dev"
	terraform -chdir=deployment/terraform/dev destroy -var="terraform_organization=$(TF_CLOUD_ORGANIZATION)" -var="image_url=ghcr.io/placeholder/steadwork" -var="image_digest=sha256:0000000000000000000000000000000000000000000000000000000000000000"

destroy-prod:
	@test -n "$(TF_CLOUD_ORGANIZATION)" || { printf '%s\n' 'Set TF_CLOUD_ORGANIZATION to your HCP Terraform organization.' >&2; exit 2; }
	@test "$(CONFIRM_PROD_DESTROY)" = "steadwork-production" || { printf '%s\n' 'This deletes the production app and database. Rerun with CONFIRM_PROD_DESTROY=steadwork-production after taking a database backup.' >&2; exit 2; }
	terraform -chdir=deployment/terraform/prod init -backend-config="organization=$(TF_CLOUD_ORGANIZATION)" -backend-config="workspaces.name=steadwork-prod"
	terraform -chdir=deployment/terraform/prod destroy -var="terraform_organization=$(TF_CLOUD_ORGANIZATION)" -var="image_url=ghcr.io/placeholder/steadwork" -var="image_digest=sha256:0000000000000000000000000000000000000000000000000000000000000000"

destroy-bootstrap:
	@test -n "$(TF_CLOUD_ORGANIZATION)" || { printf '%s\n' 'Set TF_CLOUD_ORGANIZATION to your HCP Terraform organization.' >&2; exit 2; }
	terraform -chdir=deployment/terraform/bootstrap init -backend-config="organization=$(TF_CLOUD_ORGANIZATION)" -backend-config="workspaces.name=steadwork-bootstrap"
	terraform -chdir=deployment/terraform/bootstrap destroy -var="project_name=steadwork"

# One-command local setup: dependencies, SQLite schema, then both services.
run: install
	@cd backend && uv run alembic upgrade head
	@$(MAKE) --no-print-directory dev

# The full command intentionally runs each suite in this order: frontend,
# backend, then the isolated Compose-backed browser suite.
test:
	@$(MAKE) --no-print-directory test-frontend || { status=$$?; printf '%s\n' "FAILED: frontend test stage (exit $$status)" >&2; exit "$$status"; }
	@$(MAKE) --no-print-directory test-backend || { status=$$?; printf '%s\n' "FAILED: backend test stage (exit $$status)" >&2; exit "$$status"; }
	@$(MAKE) --no-print-directory e2e || { status=$$?; printf '%s\n' "FAILED: Playwright E2E stage (exit $$status)" >&2; exit "$$status"; }

test-fast:
	@$(MAKE) --no-print-directory test-frontend || { status=$$?; printf '%s\n' "FAILED: frontend test stage (exit $$status)" >&2; exit "$$status"; }
	@$(MAKE) --no-print-directory test-backend || { status=$$?; printf '%s\n' "FAILED: backend test stage (exit $$status)" >&2; exit "$$status"; }

test-frontend:
	@printf '%s\n' '== Frontend Vitest and live API integration suite =='
	@if (cd frontend && STEADWORK_STORE=inmemory $(FRONTEND_TEST_COMMAND)); then :; else status=$$?; printf '%s\n' "Frontend test command failed (exit $$status)" >&2; exit "$$status"; fi

test-backend:
	@printf '%s\n' '== Backend pytest suite =='
	@if $(BACKEND_TEST_COMMAND); then :; else status=$$?; printf '%s\n' "Backend pytest command failed (exit $$status)" >&2; exit "$$status"; fi

e2e:
	@printf '%s\n' '== Playwright E2E suite (isolated Docker Compose project) =='
	@cd e2e && PLAYWRIGHT_BROWSERS_PATH="$(PLAYWRIGHT_BROWSERS_PATH)" npm test

e2e-install:
	@cd e2e && npm ci && PLAYWRIGHT_BROWSERS_PATH="$(PLAYWRIGHT_BROWSERS_PATH)" npx playwright install chromium

test-setup:
	@$(MAKE) --no-print-directory install
	@$(MAKE) --no-print-directory e2e-install

stop cleanup:
	@set -eu; \
	for service in frontend backend; do \
		pid_file="$(STATE_DIR)/$$service.pid"; \
		if [ -f "$$pid_file" ]; then \
			pid=$$(cat "$$pid_file"); \
			kill -TERM "-$$pid" 2>/dev/null || true; \
			printf '%s\n' "Stopped $$service process group (pid $$pid)"; \
		fi; \
	done; \
	rm -f "$(STATE_DIR)"/*.pid "$(STATE_DIR)"/*.status
