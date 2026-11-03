terraform {
  backend "remote" {
    workspaces {
      name = "steadwork-prod"
    }
  }
}

# Render permits only one active free Postgres database per workspace. Until a
# paid production DB is available, prod reuses the dev DB. To separate later,
# remove this data source and the existing_database_url module argument, then
# let the environment module create a dedicated production database.
data "terraform_remote_state" "development" {
  backend = "remote"
  config = {
    organization = var.terraform_organization
    workspaces = { name = "steadwork-dev" }
  }
}

module "environment" {
  source                  = "../environment"
  terraform_organization  = var.terraform_organization
  environment_name        = "production"
  image_url               = var.image_url
  image_digest            = var.image_digest
  region                  = var.region
  web_plan                = var.web_plan
  postgres_plan           = var.postgres_plan
  existing_database_url   = data.terraform_remote_state.development.outputs.database_url
  reuse_existing_database = true
  allowed_hosts            = var.allowed_hosts
}

output "service_url" { value = module.environment.service_url }
