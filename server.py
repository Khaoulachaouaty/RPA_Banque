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
        # Support both JSON (Bonita) and Form-Data (Web Form)
        if request.is_json:
            client_data = request.get_json()
            data_to_save = json.dumps(client_data, ensure_ascii=False)
        else:
            data = request.form.get('clientData')
            if not data:
                return jsonify({"error": "Aucune donnée client reçue"}), 400
            client_data = json.loads(data)
            data_to_save = data
        
        cin_num = client_data.get('CINNum', 'UNKNOWN')
        case_id = client_data.get('caseId', 'NONE')
        
        # Save JSON file for UiPath
        json_path = os.path.join(INPUT_DIR, f"{cin_num}_Demande.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(data_to_save)
            
        # Handle Base64 Documents (from Bonita)
        if request.is_json:
            import base64
            # Handle CIN
            cin_b64 = client_data.get('CIN_Base64')
            if cin_b64:
                try:
                    with open(os.path.join(INPUT_DIR, f"{cin_num}_CIN.jpg"), "wb") as fh:
                        fh.write(base64.b64decode(cin_b64))
                except: pass
            # Handle Domicile
            dom_b64 = client_data.get('DOM_Base64')
            if dom_b64:
                try:
                    with open(os.path.join(INPUT_DIR, f"{cin_num}_DOM.jpg"), "wb") as fh:
                        fh.write(base64.b64decode(dom_b64))
                except: pass
            # Handle Selfie
            sel_b64 = client_data.get('SEL_Base64')
            if sel_b64:
                try:
                    with open(os.path.join(INPUT_DIR, f"{cin_num}_SEL.jpg"), "wb") as fh:
                        fh.write(base64.b64decode(sel_b64))
                except: pass
            # Handle Revenu
            rev_b64 = client_data.get('REV_Base64')
            if rev_b64:
                try:
                    with open(os.path.join(INPUT_DIR, f"{cin_num}_REV.jpg"), "wb") as fh:
                        fh.write(base64.b64decode(rev_b64))
                except: pass
            
        for key in request.files:
            file = request.files[key]
            if file.filename:
                filename = f"{cin_num}_{key}_{file.filename}"
                file.save(os.path.join(INPUT_DIR, filename))
                
        return jsonify({"status": "Success", "message": f"Dossier {cin_num} reçu"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update', methods=['POST'])
def update_bonita():
    if request.is_json:
        data = request.get_json()
        case_id = data.get('caseId')
        status = data.get('status', 'SUCCESS')
    else:
        case_id = request.form.get('caseId') or request.args.get('caseId')
        status = request.form.get('status', 'SUCCESS')
    
    if not case_id:
        return jsonify({"error": "caseId manquant"}), 400
        
    try:
        import requests
        # Configuration Bonita (identique au CSV)
        BONITA_URL = "http://localhost:50532/bonita" # Ajustez le port si nécessaire
        USER = "install"
        PASS = "install"
        
        # 1. Login pour obtenir le cookie et le token CSRF
        session = requests.Session()
        login_url = f"{BONITA_URL}/loginservice"
        session.post(login_url, data={'username': USER, 'password': PASS, 'redirect': 'false'})
        
        token = session.cookies.get('X-Bonita-API-Token')
        
        # 2. Tenter plusieurs formats de corrélation (Bonita est extrêmement strict sur le type et la clé)
        msg_url = f"{BONITA_URL}/API/bpm/message"
        headers = {'X-Bonita-API-Token': token}
        
        payloads_to_try = [
            # 1. Type Long avec targetFlowNode (Le Case ID Bonita est un Long en Java)
            {
                "messageName": "RPA_DONE",
                "targetProcess": "Pool",
                "targetFlowNode": "Attente Robot",
                "correlations": {"caseId": {"value": str(case_id), "type": "java.lang.Long"}},
                "messageContent": {"status": {"value": status}}
            },
            # 2. Type String avec targetFlowNode
            {
                "messageName": "RPA_DONE",
                "targetProcess": "Pool",
                "targetFlowNode": "Attente Robot",
                "correlations": {"caseId": {"value": str(case_id), "type": "java.lang.String"}},
                "messageContent": {"status": {"value": status}}
            },
            # 3. Clé par défaut 'processInstanceId' (Type Long)
            {
                "messageName": "RPA_DONE",
                "targetProcess": "Pool",
                "targetFlowNode": "Attente Robot",
                "correlations": {"processInstanceId": {"value": str(case_id), "type": "java.lang.Long"}},
                "messageContent": {"status": {"value": status}}
            },
            # 4. Fallback classique (Ancien comportement)
            {
                "messageName": "RPA_DONE",
                "targetProcess": "Pool",
                "correlations": {"caseId": {"value": str(case_id), "type": "java.lang.String"}},
                "messageContent": {"status": {"value": status}}
            }
        ]
        
        success = False
        last_error = ""
        for payload in payloads_to_try:
            r = session.post(msg_url, json=payload, headers=headers)
            if r.status_code in [200, 204]:
                success = True
                print(f"[*] Corrélation Bonita réussie avec: {payload['correlations']}")
            else:
                last_error = r.text
                
        if success:
            return jsonify({"status": "Success", "message": "Message RPA_DONE reçu par Bonita"}), 200
        else:
            return jsonify({"error": f"Bonita a rejeté le message: {last_error}"}), 400
    except Exception as e:
        print(f"[*] Erreur Bonita: {e}")
        return jsonify({"error": str(e)}), 500

# Route pour servir le portail bancaire de simulation (évite les erreurs file:///)
@app.route('/portal')
def serve_portal():
    return send_from_directory(TEMPLATES_DIR, "BankingPortal.html")

@app.route('/form')
def serve_form():
    return send_from_directory(TEMPLATES_DIR, "Formulaire_Client.html")

if __name__ == '__main__':
    print(f"[*] Serveur démarré sur http://localhost:5000")
    print(f"[*] Formulaire Client : http://localhost:5000/form")
    print(f"[*] Portail Bancaire  : http://localhost:5000/portal")
    app.run(port=5000, debug=True)
