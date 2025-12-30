import requests
import json

response = requests.get('http://localhost:5000/api/hourly-activity?platform=sp&start=2025-11-01&end=2025-11-15')
data = response.json()

print(f"Total data points: {len(data)}")
print("\nFirst 5 records:")
for item in data[:5]:
    print(json.dumps(item, indent=2))
