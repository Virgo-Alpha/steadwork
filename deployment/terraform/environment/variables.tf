variable "terraform_organization" {
  type = string
}

variable "environment_name" {
  type = string
  validation {
    condition     = contains(["development", "production"], var.environment_name)
    error_message = "environment_name must be development or production."
  }
}

variable "image_url" {
  type = string
}

variable "image_digest" {
  type = string
  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.image_digest))
    error_message = "image_digest must be a sha256 digest."
  }
}

variable "region" {
  type    = string
  default = "singapore"
}

variable "web_plan" {
  type    = string
  default = "free"
}

variable "postgres_plan" {
  type    = string
  default = "free"
}

# Non-empty only when an environment reuses another Terraform workspace's DB.
# This currently lets prod share dev's sole free Render Postgres instance.
variable "existing_database_url" {
  type      = string
  default   = ""
  sensitive = true
}

variable "reuse_existing_database" {
  type    = bool
  default = false
}

variable "allowed_hosts" {
  type = string
}
