'use strict';

let pelaajat = [];
let current_pelaaja = null;
let pelaajan_merkki = null;

const peli = document.querySelector('#peli');

//----------------------KARTTA----------------------------//

//pitäisi estää 403r-virheet "karttatiilissä", ei näytä toimivan Firefoxissa, Chromessa ei näytä virheitä
L.TileLayer.prototype.options.referrerPolicy = 'strict-origin-when-cross-origin';

const map = L.map('map', {
    center: [51.505, -0.09],
    zoom: 5
});

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

//----------------------Pelaajat Merkki----------------------//

function näytä_pelaaja_kartalla() {
  if (pelaajan_merkki) {
    map.removeLayer(pelaajan_merkki);
  }
  let myIcon = L.icon({
    iconUrl: 'leaflet/images/plane.png',
    iconSize: [60, 60],
    /*iconAnchor: [22, 94],
    popupAnchor: [-3, -76],
    shadowUrl: 'my-icon-shadow.png',
    shadowSize: [68, 95],
    shadowAnchor: [22, 94]*/
  });

  pelaajan_merkki = L.marker([
      current_pelaaja.lat,
      current_pelaaja.lng,
  ],{icon: myIcon}).addTo(map);

  map.setView([current_pelaaja.lat, current_pelaaja.lng], 5);
}

//----------------Hae pelaajat----------//
async function hae_pelaajat() {
  try {
        const response = await fetch(`http://127.0.0.1:3000/haepelaajat`);
        const jsonData = await response.json();

        //console.log(jsonData);
        pelaajat = jsonData.data;

        näytä_pelaajat();

        console.log(pelaajat);
    } catch (error) {
        console.log(error.message);
    }
}

//----------------------Näytä pelaajat--------------------//
function näytä_pelaajat() {
  peli.innerHTML = '<h1>Ekolentopeli 2</h1><h2>Valitse pelaaja</h2>';

  pelaajat.forEach(p => {
    const btn = document.createElement('button');
    btn.textContent = `${p.nimi} (akku: ${p.akku})`;

    btn.onclick = () => valitse_pelaaja(p);

    peli.appendChild(btn);
    peli.appendChild(document.createElement('br'));
  });
}

function valitse_pelaaja(pelaaja) {
  current_pelaaja = pelaaja;
  hae_saa();
  näytä_peli();
  näytä_pelaaja_kartalla();
}

async function hae_saa(){
  try {
    const res = await fetch(`http://127.0.0.1:3000/saa/${current_pelaaja.sijainti}`);
    const data = await res.json();
    current_pelaaja.saa = data.saa;
    näytä_peli();
  } catch (e) {
    console.log(e);
  }
}

function näytä_peli() {
  const percent = current_pelaaja.akkumax > 0
    ? Math.max(0, Math.min(100, (current_pelaaja.akku / current_pelaaja.akkumax) * 100))
    : 0;
  let color = percent > 50 ? 'limegreen' : percent > 20 ? 'orange' : 'red';

  peli.innerHTML = `
    <div class="card">
        <h1>Ekolentopeli 2</h1>
        <h2>${current_pelaaja.nimi}</h2>
        
        <div class="battery">
          Akku: ${current_pelaaja.akku}/${current_pelaaja.akkumax}
          <div class="battery-bar">
            <div class="battery-fill" style="width:${percent}%; background:${color}"></div>
          </div>
        </div>
        <div class="info">
            <p><b>Sijainti:</b> ${current_pelaaja.sijainti}</p>
            <p><b>Eco pisteet:</b> ${current_pelaaja.ekopisteet}</p>
            <p><b>Aika:</b> ${current_pelaaja.aika}</p>
            <p><b>Maanosat:</b> ${current_pelaaja.maanosat ? current_pelaaja.maanosat.join(', ') : 'Ei vielä'}</p>
            <p class="weather">Sää: ${current_pelaaja.saa || 'Ei haettu'}</p>
        </div>
        
        <div class="buttons">
            <button onclick="liiku()">Lennä</button>
            <button onclick="takaisin()">Takaisin</button>
            <button onclick="kayta('lataa')"> Lataa akku (1p)</button>
            <button onclick="kayta('paranna')"> Paranna akkua (5p)</button>
      </div>
    </div>      
    `;
}

//-----------------------Liikettä-------------------//
async function liiku() {
  const icao = prompt("Anna ICAO-koodi: ");
  if (!icao) return;

  try {
    const response = await fetch(`http://127.0.0.1:3000/liiku`, {
      method: 'POST',
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        player_id: current_pelaaja.id,
        icao: icao.toUpperCase()
      })
    });

    const data = await response.json();
    if (data.status === 400) {
      alert(data.error);
      return;
    }
    alert(data.teksti);

  //päivitä pelajaa data
    current_pelaaja.sijainti = data.sijainti;
    current_pelaaja.akku = data.akku;
    current_pelaaja.aika = data.aika;
    current_pelaaja.lat=data.lat;
    current_pelaaja.lng = data.lng;

    if (data.maanosat) {
      current_pelaaja.maanosat = data.maanosat;
    }

  //---------------Hae Sää-----------------
  try {
    const saaRes = await fetch(`http://127.0.0.1:3000/saa/${current_pelaaja.sijainti}`);
    const saaData = await saaRes.json();

    current_pelaaja.saa = saaData.saa;
  } catch (error) {
    console.log("Sää ei saatavilla");
  }

    näytä_peli();
    näytä_pelaaja_kartalla(); //päivitä kartta

  } catch (error) {
        console.log(error);
    }
  }

function takaisin() {
  näytä_pelaajat();
}

//------------------------kayta toiminto-----------------------//
async function kayta(toiminto) {
  try {
    const id = current_pelaaja.id;
    const response = await fetch(
        `http://127.0.0.1:3000/käytä_ekopisteitä/${current_pelaaja.id}/${toiminto}`);
    const data = await response.json();

    alert(data.error || data.message || "Toiminto suoritettu");

    //päivitä pelaaja tiedot backendistä
    await hae_pelaajat();

    //valitse pelaaja uudestaan
    current_pelaaja = pelaajat.find(p => p.id === id);
    näytä_peli();
    näytä_pelaaja_kartalla();

  } catch (error) {
    console.log(error);
  }
}

hae_pelaajat();



