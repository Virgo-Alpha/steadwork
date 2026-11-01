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
	run_service() { \
		name=$$1; shift; \
		status=0; \
		( exec "$$@" ) >"$(LOG_DIR)/$$name.log" 2>&1 || status=$$?; \
		printf '%s\n' "$$status" >"$(STATE_DIR)/$$name.status"; \
		return "$$status"; \
	}; \
	run_service frontend sh -c 'cd frontend && exec npm run dev -- --port "$(FRONTEND_PORT)"' & frontend_pid=$$!; \
	run_service backend sh -c 'cd backend && exec uv run python manage.py runserver "127.0.0.1:$(BACKEND_PORT)"' & backend_pid=$$!; \
	printf '%s\n' "$$frontend_pid" >"$(STATE_DIR)/frontend.pid"; \
	printf '%s\n' "$$backend_pid" >"$(STATE_DIR)/backend.pid"; \
	cleanup() { kill "$$frontend_pid" "$$backend_pid" 2>/dev/null || true; wait "$$frontend_pid" "$$backend_pid" 2>/dev/null || true; rm -f "$(STATE_DIR)"/frontend.pid "$(STATE_DIR)"/backend.pid; }; \
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
			kill "$$pid" 2>/dev/null || true; \
			printf '%s\n' "Stopped $$service (pid $$pid)"; \
		fi; \
	done; \
	rm -f "$(STATE_DIR)"/*.pid "$(STATE_DIR)"/*.status
