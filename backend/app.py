from flask import Flask, Response
from flask_cors import CORS
import json
from database import yhteys
from geopy import distance
from flask import request, jsonify

connection = yhteys()

app = Flask(__name__)
CORS(app)

#----------------------------MAANOSAT--------------------------------#

def hae_koordinaatit(icao):
    sql = "SELECT latitude_deg, longitude_deg FROM airport WHERE ident = %s"
    kursori = connection.cursor()
    kursori.execute(sql, (icao,))
    return kursori.fetchone()

def hae_maanosat(pelaaja_id):
    sql = "SELECT continent FROM continent_reached WHERE player_id = %s"
    kursori = connection.cursor()
    kursori.execute(sql, (pelaaja_id,))
    tulos = kursori.fetchall()

    maanosat = []
    for t in tulos:
        maanosat.append(t[0])
    return maanosat

# --------------------------PELAAJAT----------------------------------#
def hae_pelaajan_kenttä(icao):
    sql = f"select * from airport where ident = '{icao}'"
    kursori = connection.cursor()
    kursori.execute(sql)
    tulos = kursori.fetchall()
    return tulos[0]

def hae_lentokentta(ident):
    kentta = """
            SELECT ident, name, latitude_deg, longitude_deg
            FROM airport
            WHERE ident = %s
        """
    kursori = connection.cursor()
    kursori.execute(kentta, (ident,))
    kenttä = kursori.fetchone()
    #print(kenttä)
    return kenttä[1]

def hae_mantere(icao):
    sql = f"select continent from airport where ident = '{icao}'"
    kursori = connection.cursor()
    kursori.execute(sql)
    tulos = kursori.fetchone()
    #print(tulos)
    return tulos[0]

def hae_maa(icao):
    sql = "SELECT country.name FROM country, airport WHERE ident = %s AND country.iso_country = airport.iso_country"
    kursori = connection.cursor()
    kursori.execute(sql, (icao,))
    maa = kursori.fetchone()
    #print(maa, icao, sql)
    return maa[0]

@app.route('/haepelaajat')
def hae_pelaajat():
    try:
        sql = f"SELECT id, screen_name, battery, batterymax, location, ecopoints, time FROM players"
        kursori = connection.cursor()
        kursori.execute(sql)
        pelaajat = kursori.fetchall()
        data = []
        for p in pelaajat:
            coords = hae_koordinaatit(p[4])
            lat = coords[0] if coords else None
            lng = coords[1] if coords else None

            data.append({
                "id": p[0],
                "nimi": p[1],
                "akku": p[2],
                "akkumax": p[3],
                "sijainti": p[4],
                "lat": lat,
                "lng": lng,
                "kenttä": hae_lentokentta(p[4]),
                "maa": hae_maa(p[4]),
                "mantere": hae_mantere(p[4]),
                "ekopisteet": p[5],
                "aika": p[6],
                "maanosat": hae_maanosat(p[0])
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

#----------------------KENTÄT------------------------#
@app.route('/haekentät/<id>')
def hae_kentät(id):
    try:
        id = id
        sql = f"select * from airport where type = 'large_airport' or continent ='AN'"
        kursori = connection.cursor()
        kursori.execute(sql)
        kentät = kursori.fetchall()
        data = []
        for k in kentät:

            data.append({
                "id": k[0],
                "ident": k[1],
                "type": k[2],
                "name": k[3],
                "latitude_deg": k[4],
                "longitude_deg": k[5],
                "elevation_ft": k[6],
                "continent": k[7],
                "iso_country": k[8],
                "iso_region": k[9],
                "municipality": k[10]
            })
        print(data)

        tilakoodi = 200
        vastaus = {
            "status": tilakoodi,
            "data": data
        }

    except ValueError:
        tilakoodi = 400
        vastaus = {
            "status": tilakoodi,
            "teksti": "Virheellinen id"
        }

    jsonvast = json.dumps(vastaus)
    return Response(response=jsonvast, status=tilakoodi, mimetype="application/json")

#-----------------------LUO PELAAJAT------------------------#
@app.route('/luopelaaja/<nimi>')
def luo_pelaaja(nimi):
    try:
        if nimi == '':
            raise TypeError
        sql = f"insert into players (screen_name) values ('{nimi}')"
        kursori = connection.cursor()
        kursori.execute(sql)
        kentät = kursori.fetchall()


        tilakoodi = 200
        vastaus = {
            "status": tilakoodi,
            "data": f"Pelaaja {nimi} luotu."
        }

    except TypeError:
        tilakoodi = 400
        vastaus = {
            "status": tilakoodi,
            "teksti": "Tyhjä nimi!"
        }

    jsonvast = json.dumps(vastaus)
    return Response(response=jsonvast, status=tilakoodi, mimetype="application/json")

#---------------------LIIKU PELAAJAT-------------------------#
@app.route('/liiku', methods=['POST'])
def liiku_pelaaja():
    try:
        data = request.get_json()

        pelaaja_id = data["player_id"]
        kohde = data["icao"]

        kursori = connection.cursor()

    #Get player data:
        sql = "SELECT location, battery, time FROM players WHERE id = %s"
        kursori.execute(sql, (pelaaja_id,))
        pelaaja = kursori.fetchone()
        if pelaaja is None:
            return jsonify({"status": 400, "error": "Pelaajaa ei löytynyt"}), 400

        nykyinen = pelaaja[0]
        akku = pelaaja[1]
        aika = pelaaja[2]

    #--------------coords----------------------#
        alku = hae_koordinaatit(nykyinen)
        loppu = hae_koordinaatit(kohde)

        if alku is None or loppu is None:
            return jsonify({"status": 400, "error": "Virheellinen ICAO"}), 400

        #Calculate matka
        matka_km = distance.distance(alku, loppu).km

        akku_kulutus = int(matka_km / 4)
        aika_kulutus = int(matka_km / 100 + 1)

        #Akku
        if akku < akku_kulutus:
            return jsonify({
                "status": 400,
                "error": "Akku ei riitä!"
            }), 400

        #Päivitä arvot
        uusi_akku = akku - akku_kulutus
        uusi_aika = aika - aika_kulutus

        #Hae maanosat
        sql = "SELECT continent FROM airport WHERE ident = %s"
        kursori.execute(sql, (kohde,))

        row = kursori.fetchone()
        if row is None:
            return jsonify({
                "status": 400,
                "error": "Continent not found."
            }), 400
        continent = row[0]

        #Onks saavutus?
        sql = "SELECT * FROM continent_reached WHERE player_id = %s AND continent = %s"
        kursori.execute(sql, (pelaaja_id, continent))
        exists = kursori.fetchone()

        if exists is None:
            sql = "INSERT INTO continent_reached (player_id, continent) VALUES (%s, %s)"
            kursori.execute(sql, (pelaaja_id, continent))

#-----------------Päivitä pelaajat-----------------#

        sql = """
        UPDATE players
        SET location = %s, battery = %s, time = %s
        WHERE id = %s
        """
        kursori.execute(sql, (kohde, uusi_akku, uusi_aika, pelaaja_id))
        coords = loppu

        return jsonify({
            "status": 200,
            "teksti": f"Lennettiin {int(matka_km)} km",
            "sijainti": kohde,
            "lat": coords[0],
            "lng": coords[1],
            "akku": uusi_akku,
            "aika": uusi_aika,
            "maanosat" : hae_maanosat(pelaaja_id)
        })

    except Exception as e:
        return jsonify({
            "status": 400,
            "error": str(e)
        }), 400
#---------------------KÄYTÄ EKOPOINTSEJA-------------------------#
@app.route('/käytä_ekopisteitä/<int:pelaaja_id>/<toiminto>')
def kayta_ekopisteita(pelaaja_id, toiminto):
    try:
        sql = f"SELECT ecopoints, battery, batterymax FROM players WHERE id = '{pelaaja_id}'"
        kursori = connection.cursor()
        kursori.execute(sql)
        pelaaja = kursori.fetchone()
        if pelaaja is None:
            return {
                "status": 400,
                "error": "Pelaajaa ei löytynyt"
            }

        if toiminto == "lataa":
            if pelaaja[0] < 1:
                return {
                    "status": 400,
                    "error": "lian vähän ekopisteitä"
                }
            sql = f"UPDATE players SET battery = {pelaaja[2]}, ecopoints = {pelaaja[0]-1} WHERE id = '{pelaaja_id}'"
            kursori = connection.cursor()
            kursori.execute(sql)
            return {
                "status": 200,
                "error": "akku ladattu ekopisteillä"
            }
        elif toiminto == "paranna":
            if pelaaja[0] < 5:
                return {
                    "status": 400,
                    "error": "lian vähän ekopisteitä"
                }
            sql = f"UPDATE players SET batterymax = {pelaaja[2]+100}, ecopoints = {pelaaja[0]-5} WHERE id = '{pelaaja_id}'"
            kursori = connection.cursor()
            kursori.execute(sql)
            return {
                "status": 200,
                "error": "akku paranettu ekopisteillä"
            }

    except Exception as e:
        return {
            "status": 400,
            "error": str(e)
        }

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

#------------------------ERROR HANDLER-------------------------#
@app.errorhandler(404)
def page_not_found(virhekoodi):
    vastaus = {
        "status" : "404",
        "teksti" : "Virheellinen päätepiste"
    }
    jsonvast = json.dumps(vastaus)
    return Response(response=jsonvast, status=404, mimetype="application/json")

#----------------------SUORITA SOVELLUS-----------------------#
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000, use_reloader=False)