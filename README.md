# PKT | CLI for deploying Kubernetes clusters on Packet.net
This script launches on-demand instances and orchestrates the installation of a Kubernetes cluster.

## Public URL
To start, run the following command from a terminal window:
```
bash <(curl -s https://raw.githubusercontent.com/dwrightco1/pkt/master/pkt)
```

## Kubernetes Integration
PKT uses [CCTL](https://github.com/platform9/cctl) to deploy Kubernetes on Packet instances.

CCTL is a cluster lifecycle management tool that adopts the Kubernetes community's Cluster API and uses nodeadm and etcdadm to easily deploy and maintain highly-available Kubernetes clusters in on-premises, even air-gapped environments.  

Along with [etcdadm](https://github.com/kubernetes-sigs/etcdadm) and [nodeadm](https://github.com/platform9/nodeadm), this tool makes up _klusterkit_, which lets you create, scale, backup and restore your air-gapped, on-premise Kubernetes cluster.

## Features
* Highly-available Kubernetes control plane and etcd
* Deploy & manage secure etcd clusters
* Works in air-gapped environments
* Rolling upgrade support with rollback capability
* Flannel (vxlan) CNI backend with plans to support other CNI backends
* Backup & recovery of etcd clusters from quorum loss
* Control plane protection from low memory/cpu situations
