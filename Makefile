SHELL := /bin/sh

FRONTEND_PORT ?= 5173
BACKEND_PORT ?= 8000
STATE_DIR ?= .steadwork
LOG_DIR ?= $(STATE_DIR)/logs

.PHONY: dev frontend backend install setup stop cleanup

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
	frontend_pid=$$(start_service frontend sh -c 'cd frontend && exec npm run dev -- --port "$(FRONTEND_PORT)"'); \
	backend_pid=$$(start_service backend sh -c 'cd backend && exec uv run python manage.py runserver "127.0.0.1:$(BACKEND_PORT)"'); \
	printf '%s\n' "$$frontend_pid" >"$(STATE_DIR)/frontend.pid"; \
	printf '%s\n' "$$backend_pid" >"$(STATE_DIR)/backend.pid"; \
	stop_group() { kill -TERM "-$$1" 2>/dev/null || true; }; \
	cleanup() { stop_group "$$frontend_pid"; stop_group "$$backend_pid"; wait "$$frontend_pid" "$$backend_pid" 2>/dev/null || true; rm -f "$(STATE_DIR)"/frontend.pid "$(STATE_DIR)"/backend.pid; }; \
	trap cleanup EXIT; \
	trap 'exit 130' INT TERM; \
	while [ ! -f "$(STATE_DIR)/frontend.status" ] && [ ! -f "$(STATE_DIR)/backend.status" ]; do sleep 1; done; \
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
