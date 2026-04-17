import mysql.connector
from geopy import distance

yhteys = mysql.connector.connect(
         host='127.0.0.1',
         port= 3306,
         database='flight_game',
         user='root',
         password='kissakoira',
         autocommit=True,
         use_pure=True
         )

def hae_pelaajat():
    sql = f"SELECT id, screen_name, battery, batterymax, location, ecopoints, time FROM players"
    kursori = yhteys.cursor()
    kursori.execute(sql)
    return kursori.fetchall()


def luo_pelaaja():
    nimi = input("Anna uuden pelaajan nimi: ")
    if nimi == "":
        print("Annoit tyhjän nimen, palataan päävalikkoon.")
        return
    uusipelaaja = "insert into players (screen_name) values (%s)"
    kursori = yhteys.cursor()
    kursori.execute(uusipelaaja, (nimi,))
    #tulos = kursori.fetchall()
    print("Pelaajan luonti onnistui")
    #print(tulos)

def valitse_pelaaja():
    pelaajat = hae_pelaajat()
    if len(pelaajat) == 0:
        print("Yhtään pelaajaa ei löytynyt!")
        return None
    print("\nPelaajat:")
    for p in pelaajat:
        print(f"id: {p[0]} Pelaaja: {p[1]} (akku {p[2]}/{p[3]} Mantere: {hae_mantere(p[4])} ICAO: {p[4]}, Maa: {hae_maa(p[4])}, ekopisteet {p[5]}, Aikaa jäljellä {p[6]} tuntia.)")

    valinta = input("Anna pelaajan id: ")

    for p in pelaajat:
        if str(p[0]) == valinta:
            return{
                "id": p[0],
                "nimi": p[1],
                "akku": p[2],
                "akkumax": p[3],
                "sijainti": p[4],
                "kenttä": hae_lentokentta(p[4]),
                "maa": hae_maa(p[4]),
                "mantere": hae_mantere(p[4]),
                "ekopisteet": p[5],
                "aika": p[6],
                "maanosat": hae_maanosat(p[0])
            }
    print("Tuntematon valinta!")
    return None

def hae_pelaajan_kenttä(icao):
    sql = f"select * from airport where ident = '{icao}'"
    kursori = yhteys.cursor()
    kursori.execute(sql)
    tulos = kursori.fetchall()
    return tulos[0]

def hae_mantere(icao):
    sql = f"select continent from airport where ident = '{icao}'"
    kursori = yhteys.cursor()
    kursori.execute(sql)
    tulos = kursori.fetchone()
    #print(tulos)
    return tulos[0]

def valitse_kohde(pelaajansijainti):
    kohteet = 0
    kentät = []
    sql = f"select * from airport where type = 'large_airport' or continent ='AN'"#pitäisi tulla 496 lentokenttää
    kursori = yhteys.cursor()
    kursori.execute(sql)
    tulos = kursori.fetchall()
    pelaajankenttä = hae_pelaajan_kenttä(pelaajansijainti)
    #print(pelaajankenttä)
    for kenttä in tulos:
        if kenttä[1] == pelaajankenttä[1]:
            continue
        if distance.distance((kenttä[4], kenttä[5]), (pelaajankenttä[4], pelaajankenttä[5])).km < pelaaja["akku"] * 4:
            print(f"Mantere: {kenttä[7]}, ICAO: {kenttä[1]}, Maa: {hae_maa(kenttä[1])} Kenttä: {kenttä[3]} Etäisyys: {int(distance.distance((kenttä[4], kenttä[5]), (pelaajankenttä[4], pelaajankenttä[5])).km)} km")
            kohteet += 1
            kentät.append(kenttä[1])

    if kohteet > 0:
        kenttävalinta = input("Anna sen kentän ICAO jolle haluat lentää:\n").upper()
        if kenttävalinta == "":
            print("Annoit tyhjän valinnan, palataan pelivalikkoon.")
            return
        elif kenttävalinta not in kentät:
            print("Virheellinen ICAO annettu, palataan pelivalikkoon.")
            return
        for kenttä in tulos:
            if kenttävalinta == kenttä[1]:
                print(f"Lennetään kentälle: {kenttä[1]} {kenttä[3]}")
                matka = int(distance.distance((kenttä[4], kenttä[5]), (pelaajankenttä[4], pelaajankenttä[5])).km / 4)
                print(f"Lennettiin noin {matka * 4}km.")
                liikuta_pelaajaa(kenttä[1], matka)
                pelaaja["sijainti"] = kenttä[1]
                pelaaja["kenttä"] = kenttä[3]
                pelaaja["maa"] = hae_maa(kenttä[1])
                pelaaja["mantere"] = kenttä[7]
                pelaaja["akku"] -= matka
                pelaaja["ekopisteet"] += 5
                pelaaja["aika"] -= int(matka * 4 / 100 + 1)
                if kenttä[7] not in hae_maanosat(pelaaja["id"]):
                    sql = f"insert into continent_reached (player_id, continent) values({pelaaja['id']}, '{kenttä[7]}')"
                    kursori = yhteys.cursor()
                    kursori.execute(sql)
                    pelaaja["maanosat"].append(kenttä[7])
                    print(f"Saavutit uuden maanosan: {kenttä[7]}")
    else:
        print("Akku ei riitä lentämään millekään kentälle!")

def liikuta_pelaajaa(icao, matka):
    sql = f"update players set location = '{icao}', battery = {int(pelaaja['akku'] - matka)}, ecopoints = {pelaaja['ekopisteet'] + 5}, time = {pelaaja['aika'] - int(matka * 4 / 100 + 1)} where id = '{pelaaja['id']}'"
    kursori = yhteys.cursor()
    kursori.execute(sql)
    #tulos = kursori.fetchall()

def hae_maanosat(pelaajaid):
    sql = f" select continent from continent_reached where player_id = {pelaajaid}"
    kursori = yhteys.cursor()
    kursori.execute(sql)
    tulos = kursori.fetchall()
    maanosat = []
    if len(tulos) > 0:
        for maanosa in tulos:
            maanosat.append(maanosa[0])
    return maanosat

def hae_lentokentta(ident):
    kentta = """
            SELECT ident, name, latitude_deg, longitude_deg
            FROM airport
            WHERE ident = %s
        """
    kursori = yhteys.cursor()
    kursori.execute(kentta, (ident,))
    kenttä = kursori.fetchone()
    #print(kenttä)
    return kenttä[1]

def hae_maa(icao):
    sql = "SELECT country.name FROM country, airport WHERE ident = %s AND country.iso_country = airport.iso_country"
    kursori = yhteys.cursor()
    kursori.execute(sql, (icao,))
    maa = kursori.fetchone()
    #print(maa, icao, sql)
    return maa[0]

def lataa_akkua():
    if pelaaja["akku"] == pelaaja["akkumax"]:
        print("Akku on jo täynnä!")
        return
    try:
        tunnit = int(input("Montako tuntia ladataan(1h = 20 akkuyksikköä): "))
        lataustunnit = 0
        uusi_akku = pelaaja["akku"]
        #lisää akkua 20
        for i in range(tunnit):
            if uusi_akku > pelaaja["akkumax"]:
                continue
            uusi_akku += 20
            lataustunnit += 1
        #jos akku menee yli maksimi, aseta maksimiin
        if uusi_akku > pelaaja["akkumax"]:
            uusi_akku = pelaaja["akkumax"]
        uusi_aika = pelaaja["aika"] - lataustunnit

        sql = f"UPDATE players SET battery = {uusi_akku}, time = {uusi_aika} WHERE id = '{pelaaja['id']}'"
        kursori = yhteys.cursor()
        kursori.execute(sql)

        pelaaja["akku"] = uusi_akku
        pelaaja["aika"] = uusi_aika
        print(f"Akkua ladattu {20 * lataustunnit} akkuyksikköä. Aikaa kului {lataustunnit} tunti(a).")
    except ValueError:
        print("Et antanut numeroa! Palataan pelivalikkoon.")

def paranna_akkua():
    if pelaaja["ekopisteet"] < 5: #Tarkista jos pelaajalla riittää ekopisteitä
        print("Ei tarpeeksi ekopisteitä")
        return
    uusi_akkumax = pelaaja["akkumax"] + 100 #Laske uusi akun maksimikapasiteetti
    uusi_ekopisteet = pelaaja["ekopisteet"] - 5 #vähennetään ekopisteet

    sql = f"UPDATE players SET batterymax = {uusi_akkumax}, ecopoints = {uusi_ekopisteet} WHERE id = {pelaaja['id']}"
    kursori = yhteys.cursor()
    kursori.execute(sql)

    pelaaja["akkumax"] = uusi_akkumax
    pelaaja["ekopisteet"] = uusi_ekopisteet
    print("Akun maksimi kapasiteetti parani +100!")

def lataa_akkua_ekopisteilla():
    if pelaaja["akku"] == pelaaja["akkumax"]:
        print("Akku on jo täynnä!")
        return
    if pelaaja["ekopisteet"] <= 0: #Tarkista jos pelaajalla ekopisteitä
        print("Ei ekopisteitä!")
        return
    maara = input("Kuinka monta eko-pisteet?")
    maara = int(maara)
    if maara > pelaaja["ekopisteet"]:
        print("Ei tarpeeksi ekopisteitä!")
        return
    lisa_akku = maara * 50 # (1 ekopiste = 50 akkua)
    uusi_akku = pelaaja['akku'] + lisa_akku

    if uusi_akku > pelaaja["akkumax"]:
        uusi_akku = pelaaja["akkumax"]
    uusi_ekopisteet = pelaaja["ekopisteet"] - maara #Vähennetään ekopisteet

    sql = f"UPDATE players SET battery = {uusi_akku}, ecopoints = {uusi_ekopisteet} WHERE id = {pelaaja['id']}"
    kursori = yhteys.cursor()
    kursori.execute(sql)

    pelaaja["akku"] = uusi_akku
    pelaaja["ekopisteet"] = uusi_ekopisteet
    print(f"Akkua ladatta {lisa_akku}!")

def käytä_ekopisteitä():
    print(f"\nEkopisteiden käyttö({pelaaja['ekopisteet']})")
    print("1. Paranna akkua (+100 maksimiakkua, hinta 5 ekopistettä)")
    print("2. Lataa akkua (1 ekopiste = +50 akkua)")
    print("0. Peruuta")

    valinta = input("Valitse toiminto: ")
    if valinta == "1": #Kutsu akku parannus-funktio
        paranna_akkua()
    elif valinta == "2": #Kutsu akun lataus-funktio
        lataa_akkua_ekopisteilla()
    elif valinta == "0":
        print("Peruuta")
    else:
        print("Tuntematon valinta!")


#------------Pääohjelma-----------

pelaaja = {
    "nimi": "",
    "akku": 0,
    "akkumax": 100,
    "sijainti": "",
    "kenttä": "",
    "maa": "",
    "mantere": "EU",
    "ekopisteet": 0,
    "aika": 1920,
    "maanosat": []
}
valinta = ""
while valinta != "0":
    print("-------------------------\nLennä maailman ympäri 80:ssä päivässä ja käy kaikilla mantereilla!\n-------------------------\n")
    print("Päävalikko:")
    print("1. Jatka peliä")
    print("2. Luo uusi pelaaja")
    print("0. Poistu pelistä")

    valinta = input()
    if valinta == "1":
        pelaaja = valitse_pelaaja()
        if pelaaja is not None:
            pelivalinta = ""

            while pelivalinta != "0":
                #print(pelaaja)
                print(f"Jatketaan peliä pelaajalla: {pelaaja['nimi']}")
                print(f"\nPelaaja: {pelaaja['nimi']} Sijainti: {pelaaja['mantere']} {pelaaja['maa']}, {pelaaja['sijainti']}, {pelaaja['kenttä']}")
                print(f"Akku: {pelaaja['akku']}/{pelaaja['akkumax']} Kantama: {pelaaja['akku'] * 4}/{pelaaja['akkumax'] * 4}km Ekopisteet: {pelaaja['ekopisteet']} ")
                print(f"Aikaa jäljellä: {pelaaja['aika']} tuntia ({int(pelaaja['aika'] / 24)} päivää) Saavutetut maanosat: {pelaaja['maanosat']}")

                if pelaaja["aika"] < 1:
                    print("-------------------------\nSinulta loppui aika! Pelisi on pelattu!\n-------------------------\n")
                    pelivalinta = "0"
                elif sorted(pelaaja["maanosat"]) == sorted(["EU", "AF", "AS", "OC", "AN", "NA", "SA"]) and pelaaja["sijainti"] == "EGLL":
                    print("-------------------------\nSaavutit pelin tavoitteen! Jee!\n-------------------------\n")
                    pelivalinta = "0"
                else:
                    print("\n1. Valitse uusi sijainti")
                    print("2. Lataa akkua")
                    print("3. Käytä ekopisteitä")
                    print("0. Palaa päävalikkoon")

                    pelivalinta = input()

                    if pelivalinta == "1":
                        print("Valitse lennon kohde: ")
                        valitse_kohde(pelaaja["sijainti"])
                    elif pelivalinta == "2":
                        lataa_akkua()
                    elif pelivalinta == "3":
                        if pelaaja["ekopisteet"] == 0:
                            print("Sinulla ei ole yhtään ekopistettä.")
                            continue
                        käytä_ekopisteitä()
                    elif pelivalinta == "0":
                        print("Palataan päävalikkoon")
                    else:
                        print("Tuntematon valinta!")

    elif valinta == "2":
        luo_pelaaja()
    elif valinta == "0":
        print("Heippa")
    else:
        print("Tuntematon valinta!")