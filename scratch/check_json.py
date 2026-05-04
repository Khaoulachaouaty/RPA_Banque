import json
import os

path = r'c:\Users\Hamza\Documents\UiPath\RPA_Banque\Data\Input\14412970_Demande.json'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('--- ROOT KEYS ---')
    print(list(data.keys()))
    if 'maDemandeInput' in data:
        print('--- maDemandeInput KEYS ---')
        print(list(data['maDemandeInput'].keys()))
        print('--- EMAIL ---')
        print(f"|{data['maDemandeInput'].get('email', 'MISSING')}|")
    else:
        print('maDemandeInput NOT FOUND at root')

else:
    print('File not found')
