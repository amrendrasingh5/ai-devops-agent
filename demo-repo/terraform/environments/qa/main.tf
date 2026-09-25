module "network" {
  source = "../../modules/network"

  environment = "qa"
  vpc_cidr    = "10.99.0.0/16"
}
