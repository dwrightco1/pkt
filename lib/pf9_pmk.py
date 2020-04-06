import sys
import globals
import requests
import json
import express_cli

class PMK:
    def __init__(self, du_url, du_user, du_password, du_tenant):
        self.du_url = du_url
        self.du_user = du_user
        self.du_password = du_password
        self.du_tenant = du_tenant
        self.project_id, self.token = self.login()
        

    def validate_login(self):
        if not self.token:
            return(False)
        else:
            return(True)

    def login(self):
        url = "{}/keystone/v3/auth/tokens?nocatalog".format(self.du_url)
        body = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": { "name": self.du_user, "domain": {"id": "default"}, "password": self.du_password }
                    }
                },
                "scope": {
                    "project": {
                        "name": self.du_tenant, "domain": {"id": "default"}
                    }
                }
            }
        }

        # attempt to login to region
        try:
            resp = requests.post(url, data=json.dumps(body), headers={'content-type': 'application/json'}, verify=False)
            json_response = json.loads(resp.text)
        except:
            return(None, None)

        # check for login failure
        if not "token" in json_response:
            return(None, None)

        return(json_response['token']['project']['id'], resp.headers['X-Subject-Token'])


    def onboard_cluster(self, url, username, password, tenant, region):
        if not express_cli.validate_installation():
            sys.stdout.write("ERROR: missing pip package: express-cli\n")
        if not express_cli.build_config(url, username, password, tenant, region):
            sys.stdout.write("ERROR: failed to build express-cli config file\n")

        sys.stdout.write("\n[Onboard Kubernetes Cluster]\n")
