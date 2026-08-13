# qrsticker.py — QR code su cover per adesivi

Colloca un QR code su una copertina quadrata, misurando da solo lo spazio
libero per non finire sopra il soggetto. Pensato per stampare adesivi:
sceglie la dimensione massima che sta sul fondo pulito e verifica che il
codice risultante sia effettivamente leggibile.

Output: PNG alla risoluzione della cover originale, con il DPI corretto
già scritto nei metadati.

---

## Installazione su Windows

Serve Python 3.9 o superiore. Testato su 3.10.

Apri il terminale nella cartella dove hai messo `qrsticker.py`:

```
py -m venv .venv
.venv\Scripts\activate
pip install qrcode pillow opencv-python-headless pyzbar
```

Fatto. Su Windows le librerie C di zbar sono già dentro il pacchetto
`pyzbar`, quindi non c'è nient'altro da installare a parte.

### Se qualcosa non parte

**`ImportError` su `libzbar-64.dll` o `libiconv.dll`**
Manca il runtime Visual C++. Installa **Visual C++ Redistributable for
Visual Studio 2013** — la versione conta, pyzbar è linkato a quella e non
alle più recenti. In alternativa disinstalla pyzbar: lo script funziona
lo stesso, la verifica gira con OpenCV soltanto.

**PowerShell rifiuta di eseguire `activate`**
Nella sessione corrente:
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Oppure usa `cmd` e lancia `.venv\Scripts\activate.bat`.

**`python` apre il Microsoft Store**
Usa `py` al posto di `python`. È il launcher ufficiale e ignora gli alias
di Store.

### Dipendenze

| Pacchetto | Serve a |
|---|---|
| `qrcode` | generare la matrice del codice |
| `pillow` | leggere e comporre le immagini |
| `opencv-python-headless` | verifica di decodifica (opzionale) |
| `pyzbar` | secondo decoder di verifica (opzionale) |

Senza i due opzionali lo script genera comunque i file: al posto del
report di verifica stampa una riga che segnala che i decoder mancano.
Usa la variante `headless` di OpenCV, non `opencv-python`: la seconda
tira dentro tutto lo stack grafico Qt che qui non serve.

---

## Uso

Comando minimo:

```
py qrsticker.py cover.png --album "https://open.spotify.com/album/XXXX"
```

Con due destinazioni diverse, utile per capire quale funziona meglio:

```
py qrsticker.py cover.png --album "https://open.spotify.com/album/XXXX" --track "https://open.spotify.com/track/YYYY"
```

Metti sempre gli URL tra virgolette. In PowerShell la continuazione di
riga è il backtick, in `cmd` è `^`: se hai dubbi scrivi tutto su una
riga sola.

### Opzioni

| Opzione | Default | Cosa fa |
|---|---|---|
| `--album URL` | — | destinazione album |
| `--track URL` | — | destinazione brano |
| `--url URL` | — | destinazione generica, ripetibile |
| `--sticker-cm` | `9.3` | lato dell'adesivo stampato, in cm |
| `--position` | `both` | `tr` alto a destra, `bl` basso a sinistra, `both` |
| `--field` | `off` | `off` moduli chiari sul fondo; `on` campo chiaro con moduli scuri |
| `--size` | `auto` | footprint in cm, oppure `auto` |
| `--max-size` | `2.8` | tetto per la ricerca automatica |
| `--inset-mm` | `3.5` con campo, `2.0` senza | margine dai bordi |
| `--ec` | `M` | correzione errore: `L` `M` `Q` `H` |
| `--min-module` | `0.53` | modulo minimo accettato, in mm |
| `--outdir` | `.` | cartella di destinazione |
| `--prefix` | `qr` | prefisso dei nomi file |

### Le due varianti grafiche

`--field off` (default) disegna i moduli in bianco caldo direttamente sul
fondo della copertina, senza riquadro. Il margine di quiete è fondo
pulito, non bianco. Il codice risulta invertito rispetto allo standard:
iPhone e Android recenti lo leggono, alcune app di terze parti e Android
datati no. **Provalo sul campo prima di stampare in quantità.**

`--field on` disegna un riquadro chiaro con i moduli in rosso scuro,
margine 3,5 mm dai bordi, nello stile del codice a barre sugli albi a
fumetti. Polarità standard, quindi lo legge chiunque. È la scelta
prudente.

---

## Come sceglie la dimensione

In modalità `auto` parte da `--max-size` e scende di mezzo millimetro per
volta finché il footprint non sta interamente su fondo pulito. Il bordo
del soggetto viene misurato riga per riga dentro la fascia che il codice
occuperebbe davvero, non su un ritaglio fisso, quindi si adatta alla posa.

Se per stare nello spazio libero il modulo dovesse scendere sotto
`--min-module`, lo script si ferma e te lo dice invece di produrre un file
che non si leggerebbe. In quel caso: accorcia l'URL, cambia angolo, o
passa a `--field on` (il riquadro può stare sopra il soggetto, quindi non
ha il vincolo).

Il colore di fondo viene campionato dai quattro angoli, quindi funziona
anche su copertine che non sono rosse.

## Verifica

Ogni file prodotto viene riletto con due decoder a tre risoluzioni
decrescenti, per simulare una foto imperfetta. Quando il codice è
invertito viene invertito prima di leggerlo — altrimenti fallirebbe
sempre per polarità e la verifica non direbbe nulla su geometria,
contrasto e margini, che sono le cose che possono davvero rompersi.

Sotto 0,6 mm di modulo compare un avviso. Non significa che non funzioni,
significa che il margine si assottiglia con sporco, graffi e luce scarsa.

## Riferimenti utili

Il modulo è il quadratino elementare del codice e determina tutto. Sotto
0,5 mm i problemi iniziano su fotocamere modeste e luce artificiale.
La distanza di lettura è circa dieci volte il lato del codice: 2 cm si
legge da una ventina di centimetri, cioè chinandosi appena.

Accorciare l'URL vale più che ingrandire l'adesivo. Su un link Spotify,
togliere `?si=...` e `&utm_source=...` lo riduce di trenta caratteri e fa
scendere il codice di una versione intera, a parità di ingombro.

## Limiti noti

Il rilevamento del bordo confronta ogni pixel con il colore di fondo
usando una tolleranza fissa. Su copertine con sfumature ampie, o con
soggetto di colore vicino al fondo, può sbagliare la misura: in quei casi
forza `--size` e controlla il risultato a occhio. Su fondi piatti è
affidabile.

Lo script assume una cover quadrata. Se non lo è, avvisa e procede
calcolando tutto sulla larghezza.
