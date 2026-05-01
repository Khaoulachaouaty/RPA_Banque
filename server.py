import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Utilisation de chemins relatifs pour la portabilité
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "Data", "Input")
TEMPLATES_DIR = os.path.join(BASE_DIR, "Templates")

os.makedirs(INPUT_DIR, exist_ok=True)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.form.get('clientData')
        if not data:
            return jsonify({"error": "Aucune donnée client reçue"}), 400
        
        client_data = json.loads(data)
        cin_num = client_data.get('CINNum', 'UNKNOWN')
        
        json_path = os.path.join(INPUT_DIR, f"{cin_num}_Demande.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(data)
            
        for key in request.files:
            file = request.files[key]
            if file.filename:
                filename = f"{cin_num}_{key}_{file.filename}"
                file.save(os.path.join(INPUT_DIR, filename))
                
        return jsonify({"status": "Success", "message": f"Dossier {cin_num} reçu"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route pour servir le portail bancaire de simulation (évite les erreurs file:///)
@app.route('/portal')
def serve_portal():
    return send_from_directory(TEMPLATES_DIR, "BankingPortal.html")

if __name__ == '__main__':
    print(f"[*] Serveur démarré sur http://localhost:5000")
    print(f"[*] Portail disponible sur http://localhost:5000/portal")
    app.run(port=5000, debug=True)
