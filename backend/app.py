from flask import Flask, Response
from flask_cors import CORS
import json
from database import yhteys
from flask import request, jsonify

connection = yhteys()

app = Flask(__name__)
CORS(app)
@app.route('/haepelaajat')
def hae_pelaajat():
    try:
        sql = "SELECT id, screen_name, battery, batterymax, location, ecopoints, time FROM players"
        kursori = connection.cursor()
        kursori.execute(sql)
        pelaajat = kursori.fetchall()
        data = []
        for p in pelaajat:
            data.append({
                "id": p[0],
                "nimi": p[1],
                "akku": p[2],
                "akkumax": p[3],
                "sijainti": p[4],
                #"kenttä": hae_lentokentta(p[4]),
                #"maa": hae_maa(p[4]),
                #"mantere": hae_mantere(p[4]),
                "ekopisteet": p[5],
                "aika": p[6],
                #"maanosat": hae_maanosat(p[0])
            })
        #print(data)

        tilakoodi = 200
        vastaus = {
            "status": tilakoodi,
            "data": data
        }

    except ValueError:
        tilakoodi = 400
        vastaus = {
            "status": tilakoodi,
            "teksti": "Virheellinen "
        }

    jsonvast = json.dumps(vastaus)
    return Response(response=jsonvast, status=tilakoodi, mimetype="application/json")

"""@app.route('/summa/<luku1>/<luku2>')
def summa(luku1, luku2):
    try:
        luku1 = float(luku1)
        luku2 = float(luku2)
        summa = luku1+luku2

        tilakoodi = 200
        vastaus = {
            "status": tilakoodi,
            "luku1": luku1,
            "luku2": luku2,
            "summa": summa
        }

    except ValueError:
        tilakoodi = 400
        vastaus = {
            "status": tilakoodi,
            "teksti": "Virheellinen yhteenlaskettava"
        }

    jsonvast = json.dumps(vastaus)
    return Response(response=jsonvast, status=tilakoodi, mimetype="application/json")"""

@app.errorhandler(404)
def page_not_found(virhekoodi):
    vastaus = {
        "status" : "404",
        "teksti" : "Virheellinen päätepiste"
    }
    jsonvast = json.dumps(vastaus)
    return Response(response=jsonvast, status=404, mimetype="application/json")

@app.route('/liiku', methods=['POST'])
def liiku_pelaaja():
    try:
        data = request.get_json()

        pelaaja_id = data["player_id"]
        icao = data["icao"]

        sql = "UPDATE players SET location = %s WHERE id = %s"
        kursori = connection.cursor()
        kursori.execute(sql, (icao, pelaaja_id))

        vastaus = {
            "status": 200,
            "teksti": f"Lennettiin kentälle {icao}",
            "sijainti": icao
        }

        return jsonify(vastaus), 200

    except Exception as e:
        return jsonify({
            "status": 400,
            "error": str(e)
        }), 400


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000)