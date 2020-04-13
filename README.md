# PKT | CLI for deploying Kubernetes clusters on Packet.net
PKT launches bare-metal instances on [Packet.Net](https://app.packet.net) and orchestrates the installation of a Kubernetes cluster.

## Public URL
To start, run the following command from a Bash shell prompt:
```
/bin/bash <(curl -s https://raw.githubusercontent.com/dwrightco1/pkt/master/pkt)
```

To re-init the installation, add the '-i' option:
```
bash <(curl -s https://raw.githubusercontent.com/dwrightco1/pkt/master/pkt) -i
```

## Kubernetes Integration
PKT uses [Express-CLI](https://github.com/platform9/express-cli) to deploy Kubernetes on bare-metal [Packet.Net](https://app.packet.net) instances using [Platform9 PMK](https://platform9.com/signup)

## Kubernetes Cluster Deployment
A cluster is deployed by running `pkt --apply <spec-file>`

The `<spec-file>` is used to describe the details of the Packet bare-metal instances (to be used as Kubernetes cluster nodes), the credentials for the Platform9 SaaS control plane, as well as the details of the Kubernetes cluster.

Here is an example `<spec-file>`:
```
{
  "actions": [
      {
          "operation": "launch-instance",
          "num_instances": 1,
          "hostname_base": "<hostname-base> (note: will be appended with '01', '02', etc.)",
          "plan": "<planName>",
          "facility": "<facilityName>",
          "operating_system": "<osName>",
          "userdata": "",
          "customdata": "",
          "network_mode": "<layer3|hybrid>",
          "k8s_vlan_tag": "<descr-on-vlan> (note: place this text in the 'Description' field of the VLAN)",
          "ip_addresses": [
              {
                  "address_family": 4,
                  "public": false
              },
              {
                  "address_family": 4,
                  "public": true
              },
              {
                  "address_family": 6,
                  "public":true
              }
          ]
      },
      {
          "operation": "pf9-build-cluster",
          "pmk_region": {
            "url": "<region-url>",
            "username": "<region-username>",
            "password": "<region-password> (note: must be encrypted using 'pkt -e')",
            "tenant": "<region-tenant>",
            "region": "<region-name>"
          },
          "ssh_username" : "<username-for-ssh-access>",
          "ssh_key" : "<path-to-ssh-privateKey>",
          "cluster": {
            "name": "<cluster-name>",
            "master_vip_ipv4": "<vip-ip>",
            "master_vip_iface": "<vip-interfaceName>",
            "metallb_cidr": "<startIp>-<endIp>",
            "containers_cidr": "192.168.0.0/16",
            "services_cidr": "192.169.0.0/16",
            "privileged": 0,
            "app_catalog_enabled": 0,
            "allow_workloads_on_master": 0
          }
      }
  ]
}
```
