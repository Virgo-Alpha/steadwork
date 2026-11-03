terraform {
  backend "remote" {
    workspaces {
      name = "steadwork-dev"
    }
  }
}

module "environment" {
  source                = "../environment"
  terraform_organization = var.terraform_organization
  environment_name      = "development"
  image_url             = var.image_url
  image_digest          = var.image_digest
  region                = var.region
  web_plan              = var.web_plan
  postgres_plan         = var.postgres_plan
  allowed_hosts         = var.allowed_hosts
}

output "service_url" { value = module.environment.service_url }
