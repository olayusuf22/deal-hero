import requests
from pprint import pprint


# Structure payload.
payload = {
    'source': 'amazon_search',
    'domain_name': 'usa',
    'query': 'nirvana tshirt',
    'start_page': 2,
    'pages': 2,
    'parse': True,
    'context': [
        {'key': 'category_id', 'value': 16391693031}
    ],
}


# Get response.
response = requests.request(
    'POST',
    'https://realtime.oxylabs.io/v1/queries',
    auth=('batman_WI3g8', 'Team4batman23456_'),
    json=payload,
)

# Print prettified response to stdout.
pprint(response.json())