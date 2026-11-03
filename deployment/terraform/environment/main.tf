terraform {
  required_version = ">= 1.6.0"
  required_providers {
    render = {
      source  = "render-oss/render"
      version = "~> 1.9.1"
    }
  }
}

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
  # Render allows only one active free Postgres database per workspace. Prod
  # supplies the dev database URL and skips this resource; remove the conditional
  # and use a dedicated database when production isolation is available.
  count          = var.reuse_existing_database ? 0 : 1
  name           = "${local.service_name}-db"
  plan           = var.postgres_plan
  region         = var.region
  version        = "17"
  database_name  = "steadwork"
  database_user  = "steadwork"
  environment_id = local.environment_id
}

# Preserve the existing development database in Terraform state when moving
# this resource to count-based creation for the shared free-tier configuration.
moved {
  from = render_postgres.database
  to   = render_postgres.database[0]
}

locals {
  database_url = var.reuse_existing_database ? var.existing_database_url : render_postgres.database[0].connection_info.internal_connection_string
}

resource "render_web_service" "app" {
  name               = local.service_name
  plan               = var.web_plan
  region             = var.region
  environment_id     = local.environment_id
  health_check_path  = "/api/health/"
  runtime_source = {
    image = {
      image_url = var.image_url
      digest    = var.image_digest
    }
  }

  env_vars = {
    DATABASE_URL = { value = local.database_url }
    STEADWORK_STORE = { value = "postgresql" }
    DJANGO_DEBUG = { value = "false" }
    DJANGO_SECRET_KEY = { generate_value = true }
    DJANGO_ALLOWED_HOSTS = { value = var.allowed_hosts }
  }

  # The Render Terraform provider currently includes maintenance_mode in
  # updates even when unset, which Render rejects for free services. Terraform
  # creates the service; CI uses Render's API/CLI for later changes and deploys.
  lifecycle {
    ignore_changes = all
  }
}

output "service_id" {
  value = render_web_service.app.id
}

output "service_url" {
  value = render_web_service.app.url
}

output "database_name" {
  value = var.reuse_existing_database ? "steadwork-development-db" : render_postgres.database[0].name
}

output "database_url" {
  value     = local.database_url
  sensitive = true
}
