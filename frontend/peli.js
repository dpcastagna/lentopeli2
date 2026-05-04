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
  näytä_peli();
  näytä_pelaaja_kartalla();
}

function näytä_peli() {
  peli.innerHTML = `
        <h1>Ekolentopeli 2</h1>
        <h2>${current_pelaaja.nimi}</h2>
        <p>Akku: ${current_pelaaja.akku}/${current_pelaaja.akkumax}</p>
        <p>Sijainti: ${current_pelaaja.sijainti}</p>
        <p>Eco pisteet: ${current_pelaaja.ekopisteet}</p>
        <p>Aika: ${current_pelaaja.aika}</p>
        <p>Maanosat: ${current_pelaaja.maanosat ? current_pelaaja.maanosat.join(', ') : 'Ei vielä'}</p>
        
        <button onclick="liiku()">Lennä</button>
        <button onclick="takaisin()">Takaisin</button>
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
    näytä_peli();
    näytä_pelaaja_kartalla(); //päivitä kartta

  } catch (error) {
        console.log(error);
    }
  }

function takaisin() {
  näytä_pelaajat();
}

hae_pelaajat();



