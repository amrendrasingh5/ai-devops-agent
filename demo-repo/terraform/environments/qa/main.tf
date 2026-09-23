module "network" {
  source = "../../modules/network"

  environment = "qa"
  vpc_cidr    = "10.20.0.0/16"
}
