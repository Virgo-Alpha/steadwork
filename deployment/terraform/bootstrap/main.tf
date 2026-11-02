terraform {
  required_version = ">= 1.6.0"
  required_providers {
    render = {
      source  = "render-oss/render"
      version = "~> 1.9.1"
    }
  }
  backend "remote" {}
}

provider "render" {}

resource "render_project" "steadwork" {
  name = var.project_name
  environments = {
    development = {
      name             = "development"
      protected_status = "unprotected"
    }
    production = {
      name             = "production"
      protected_status = "protected"
    }
  }
}

output "project_id" {
  value = render_project.steadwork.id
}

output "development_environment_id" {
  value = render_project.steadwork.environments["development"].id
}

output "production_environment_id" {
  value = render_project.steadwork.environments["production"].id
}
