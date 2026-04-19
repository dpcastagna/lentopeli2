'use strict';

let pelaajat = [];

async function hae_pelaajat() {
  try {
        const response = await fetch(`http://127.0.0.1:5000/haepelaajat`);
        const jsonData = await response.json();

        //console.log(jsonData);
        pelaajat = jsonData.data;

        console.log(pelaajat);
    } catch (error) {
        console.log(error.message);
    }
}
hae_pelaajat();

const peli = document.querySelector('#peli');

peli.innerHTML += "jee";