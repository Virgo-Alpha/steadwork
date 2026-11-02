terraform {
  required_version = ">= 1.6.0"
  required_providers {
    render = {
      source  = "render-oss/render"
      version = "~> 1.9.1"
    }
  }
}

provider "render" {}

data "terraform_remote_state" "bootstrap" {
  backend = "remote"
  config = {
    organization = var.terraform_organization
    workspaces = { name = "steadwork-bootstrap" }
  }
}

locals {
  environment_id = var.environment_name == "development" ? data.terraform_remote_state.bootstrap.outputs.development_environment_id : data.terraform_remote_state.bootstrap.outputs.production_environment_id
  service_name   = "steadwork-${var.environment_name}"
}

resource "render_postgres" "database" {
  name           = "${local.service_name}-db"
  plan           = var.postgres_plan
  region         = var.region
  version        = "17"
  database_name  = "steadwork"
  database_user  = "steadwork"
  environment_id = local.environment_id
}

resource "render_web_service" "app" {
  name               = local.service_name
  plan               = var.web_plan
  region             = var.region
  environment_id     = local.environment_id
  health_check_path  = "/api/health/"
  pre_deploy_command = "uv run --no-sync alembic upgrade head"

  runtime_source = {
    image = {
      image_url = var.image_url
      digest    = var.image_digest
    }
  }

  env_vars = {
    DATABASE_URL = { value = render_postgres.database.connection_info.internal_connection_string }
    STEADWORK_STORE = { value = "postgresql" }
    DJANGO_DEBUG = { value = "false" }
    DJANGO_SECRET_KEY = { generate_value = true }
    DJANGO_ALLOWED_HOSTS = { value = var.allowed_hosts }
  }
}

output "service_url" {
  value = render_web_service.app.url
}

output "database_name" {
  value = render_postgres.database.name
}
