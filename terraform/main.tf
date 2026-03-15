terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project" {}
variable "region" {}
variable "environment" {}
variable "telegram_bot_token" { sensitive = true }
variable "gemini_api_key" { sensitive = true }

provider "google" {
  project = var.project
  region  = var.region
}

module "secrets" {
  source = "./modules/secrets"
  project = var.project
  secrets = {
    "TELEGRAM_BOT_TOKEN" = var.telegram_bot_token
    "GEMINI_API_KEY"     = var.gemini_api_key
  }
}

module "cloud_run" {
  source = "./modules/cloud_run"
  project = var.project
  region  = var.region
  environment = var.environment
  service_account_email = module.iam.service_account_email
}

module "iam" {
  source = "./modules/iam"
  project = var.project
}
