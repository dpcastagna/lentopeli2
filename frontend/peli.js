'use strict';

let pelaajat = [];
let current_pelaaja = null;

const peli = document.querySelector('#peli');

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

function näytä_pelaajat() {
  peli.innerHTML = '<h1>Ekolentopeli 2</h1><h2>Valitse pelajaa</h2>';

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

    if (data.maanosat) {
      current_pelaaja.maanosat = data.maanosat;
    }
    näytä_peli();

  } catch (error) {
        console.log(error);
    }
  }

function takaisin() {
  näytä_pelaajat();
}

hae_pelaajat();



