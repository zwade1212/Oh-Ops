#!/home/jenkins/pyenv/bin/python

import boto3
import requests
import json
import sys
import time

# CloudFront and Cloudflare domain mappings
cloudflare_domains = { 
                       'ax.com': '001f4xxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                       'bx.co.ke': '9c37xxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                       'cx.com': 'e63bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                     }

cloudfront_domains = {
                       't1.com.ng': 'Exxxxxxxxxxxxx', 
                       'b5.com': 'Exxxxxxxxxxxxx',
                       'w1.com|w2.co.ug|w3.com|w4.com': 'zzzzzzzzzzzzzz',
                       'a1.com.ng|a2.com.ng': 'Exxxxxxxxxxxxx', 
                       'c3.com': 'Exxxxxxxxxxxxx', 
                       'cax.com': 'Ezzzzzzzzzzzzzz', 
                     }

# Cloudflare API credentials
cloudflare_email = 'zhaoruwei@luckybus.me'
cloudflare_api_key = '1d1df5758aead11bbda59a16b08e861b48aed'

def refresh_cloudfront(domain):
    ts = int(time.time())
    client = boto3.client('cloudfront')
    distribution_id = cloudfront_domains[domain]
    response = client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': ['/*']
            },
            'CallerReference': f'devops_{ts}'
        }
    )
    print(f'CloudFront invalidation for {domain} initiated: {response["Invalidation"]["Id"]}')

def refresh_cloudflare(domain):
    zone_id = cloudflare_domains[domain]
    url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache'
    headers = {
        'X-Auth-Email': cloudflare_email,
        'X-Auth-Key': cloudflare_api_key,
        'Content-Type': 'application/json'
    }
    data = {
        'purge_everything': True
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200 and response.json()["success"]:
        print(f'Cloudflare cache for {domain} purged successfully.')
    else:
        print(f'Failed to purge Cloudflare cache for {domain}: {response.text}')

def main(domains_string):
    domains = domains_string.split(',')
    for domain in domains:
        if domain in cloudfront_domains:
            refresh_cloudfront(domain)
        elif domain in cloudflare_domains:
            refresh_cloudflare(domain)
        else:
            print(f'No CDN configuration found for {domain}')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python flush_cdn.py 'a.com,b.com,c.com'")
        sys.exit(1)

    domain_input = sys.argv[1]
    main(domain_input)

