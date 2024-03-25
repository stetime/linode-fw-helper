import os
import requests
from linode_api4 import LinodeClient
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("LINODE_API_KEY")


def get_local_ip():
    try:
        url = "https://api64.ipify.org?format=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data["ip"]
        else:
            print(f"failed to get ip address from ipify.org, status code: {response.status_code}")
    except Exception as e:
        print(f"error: {e}")


def get_linode_ips(client):
    linodes = client.linode.instances()
    return [ipv4 for linode in linodes for ipv4 in linode.ipv4]

def update_remote_fw(client, ip):
    try:
        local_ip = f"{ip}/32"
        firewall = client.networking.firewalls()[0]
        rules = {
            "inbound": [
                {
                    "action": "ACCEPT",
                    "addresses": {
                        "ipv4": [
                            local_ip
                        ]
                    },
                    "description": "allow all TCP from local ip",
                    "label": "allow-all-tcp-local",
                    "ports": "1-65535",
                    "protocol": "TCP"
                },
                {
                    "action": "ACCEPT",
                    "addresses": {
                        "ipv4": [
                            local_ip
                        ]
                    },
                    "description": "allow all UDP from local ip",
                    "label": "allow-all-udp-local",
                    "ports": "1-65535",
                    "protocol": "UDP"
                }
            ]
        }
        firewall.update_rules(rules)
        print(f"ip address has changed to {ip}, firewall rules updated")
    except Exception as e:
        print(f"error updating firewall rules: {e}")


def main():
    if api_key is None or api_key == "":
        print("This script requires a valid Linode API key")
        print("You can generate one at https://cloud.linode.com/profile/tokens")
        return
    
    client = LinodeClient(api_key)
    current_ip = get_local_ip()

    if current_ip in get_linode_ips(client):
        print("Your current IP matches a Linode. You are almost certainly using your VPN already")
        return

    try:
        with open('ip.txt', 'r') as file:
            stored_ip = file.read()
    except FileNotFoundError:
        stored_ip = None
    
    if current_ip != stored_ip:
        update_remote_fw(client, current_ip)
        with open('ip.txt', 'w') as file:
            file.write(current_ip)
    else:
        print("ip address hasn't changed")

if __name__ == '__main__':
    main()
