variable "terraform_organization" { type = string }
variable "image_url" { type = string }
variable "image_digest" { type = string }
variable "region" {
  type    = string
  default = "singapore"
}
variable "web_plan" {
  type    = string
  default = "starter"
}
variable "postgres_plan" {
  type    = string
  default = "basic_256mb"
}
variable "allowed_hosts" {
  type    = string
  default = "steadwork-production.onrender.com"
}
