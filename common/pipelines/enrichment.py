import requests

def cas_lookup(cas):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{cas}/JSON"
    r = requests.get(url, timeout=5)
    if r.status_code == 200:
        return r.json()
    return None