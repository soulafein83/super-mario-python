# Plan: Super Mario (Python/pygame) — poprawki i rozwinięcie gry

> Dokument planu: przegląd dokumentacji i kodu, **zweryfikowane** problemy
> (odnośniki `plik:wiersz`) oraz fazy rozwoju. Stwierdzenia oznaczone
> „zweryfikowano” sprawdzono headless (`SDL_VIDEODRIVER=dummy`,
> `SDL_AUDIODRIVER=dummy`) — nie są cytowane z `wnioski.md`.

---

## 1. Streszczenie

Projekt to data-driven reimplementacja Super Mario Bros (Python/pygame,
okno 640×480, 60 FPS, grid kafli 32×32, poziomy w JSON). Jądro działa:
poziom 1-1 ładuje się (długość 60, 37 encji), encje się aktualizują,
menu, pauza i rozmycie (Gaussian blur) działają.

Problemy:

- **Czysta instalacja wg README nie działa** — `requirements.txt` pakuje
  `pygame==2.0.0.dev10` i `scipy==1.4.1`; na współczesny Python (tu 3.14.8)
  nie ma dla nich wheels. Lokalnie zainstalowane są pygame-ce 2.5.7 +
  scipy 1.18.1 i gra **działa headless** — twierdzenie z `wnioski.md`,
  że „gra nie uruchamia się”, jest prawdziwe tylko dla świeżej instalacji.
- **Zamrożenie ekranu na końcu poziomu** (brak flagi: Mario dochodzi do
  prawej krawędzi, kamera się blokuje, `Level.drawLevel` cicho wyłazi z
  pętli na `IndexError`) — zweryfikowano.
- **Błąd `EntityCollider.determineSide`** (dzielenie współrzędnych
  ekranowych przez 2 przed `collidepoint` → niepoprawne wykrywanie
  „lądowania na wrogu”) — zweryfikowano.
- **Niekonsekwentna konwencja współrzędnych encji** (JSON `[wiersz, kolumna]`
  dla mobów, `[kolumna, wiersz]` dla przedmiotów + zamienione argumenty
  w `super().__init__`) — działa tylko dzięki wzajemnemu skompensowaniu;
  zweryfikowano testem spawnów.
- **Brak pętli gry**: brak zwycięstwa, żyć, odliczania czasu i
  przechodzenia poziomów (timer liczy w górę).
- **Level1-2.json nie ma bloku `entities`** → poziom ładuje się bez
  żadnej encji (błąd cicho pochłonięty) — zweryfikowano.

Plan: 5 faz — **A** stabilizacja (P0+P1), **B** pełna pętla gry
(fuga → flaga, życia, timer, postęp), **C** zawartość (poziomy,
fire flower, Yoshi, łamanie cegieł), **D** dopracowanie (blur bez
scipy, cache fontu, głośność), **E** infrastruktura (pytest headless,
CI, ruff, README). Kolejność zadań w §6.

## 2. Środowisko i metodologia weryfikacji

Środowisko (sprawdzone):

- Python 3.14.8; pygame-ce 2.5.7 (SDL 2.32.74) zainstalowane jako moduł
  `pygame`; scipy 1.18.1.
- Gra działa headless: poziom 1-1 ładuje się (długość 60, 37 encji),
  `drawLevel` + 120 klatek aktualizacji encji — OK, `GaussianBlur` — OK.
- Git: 10 plików z niezacommitowanymi zmianami (refaktor BASE_DIR,
  niedokończony — patrz P0.2), `wnioski.md` untracked, `settings.json`
  gitignored (brak w repo).

Metoda: przeczytano całą dokumentację (README, wnioski.md), wszystkie
źródła (33 pliki `.py`), poziomy i sprite JSON-y; następnie testy
weryfikacyjne headless (skrypty w `/tmp/opencode/`: `smoke_test.py`,
`blur_test.py`, `verify_test.py`, `spawn_test.py`).

## 3. Architektura (skróconie)

```
main.py               pętla gry: menu → poziom; Dashboard, Sound, Level, Menu, Mario
compile.py            pakowanie py2exe (zepsute — P3.1)
requirements.txt      pinowanie: pygame 2.0.0.dev10, scipy 1.4.1 (P0.1)
classes/              silnik: Dashboard, Font, Camera, Input, Level, Maths,
                      Menu, Pause, Sound, Sprite, Sprites, Spritesheet, Tile,
                      Animation, GaussianBlur, Collider, EntityCollider
entities/             EntityBase + Mario, Goomba, Koopa, Mushroom, Coin,
                      CoinBox, CoinBrick, RandomBox, Item
traits/               jump, go (ruch), leftrightwalk, bounce
levels/               Level1-1.json (kompletny), Level1-2.json (bez entities — P1.7)
sprites/              7 sprite JSON (kafle, postacie, przedmioty, tło)
img/, sfx/            zasoby
settings.json         przełączniki muzyki/sfx (gitignored)
```

Przepływ danych: `Level.loadLevel` czyta JSON → grid `self.level`
(15 wierszy × długość kolumn) + `entityList`. `Level.drawLevel(camera)`
rysuje widoczne kafle i **wewnątrz wywołuje `updateEntities`**
(oddzielanie renderu od symulacji — P2.6). `Mario.update()` = fizyka →
kamera → kolizje → (na końcu) wejście (P1.5). Kolizje z gridem:
`Collider` (najpierw X, potem Y); z encjami: `EntityCollider` (tylko
Mario — moby się nie widzą, P2.7).

Kluczowe konwencje (ważne przy nowych poziomach):

- Podłoże: w JSON `y: [14, 16]`, ale kafle kolizji generowane są z
  przesunięciem `(y-1)*32` (classes/Level.py:52-61) → podłoże
  „zajmuje w praktyce” wiersze 13-14.
- Kamera: `pos.x` jest ujemnym przesunięciem w kafle; pozycja blitu =
  `(x + camera.pos.x) * 32`.
- Usuwane encje: sentinel `alive = None` (classes/Level.py:84).

---

## 4. Znalezione problemy (zweryfikowane), wg priorytetu

### P0 — uruchamialność

| # | Problem | Gdzie | Poprawka |
|---|---------|-------|----------|
| P0.1 | `requirements.txt`: `pygame==2.0.0.dev10`, `scipy==1.4.1` — brak wheels na współczesny Python (tu 3.14.8); świeża instalacja wg README nie powstanie | requirements.txt:1-2 | `pygame-ce>=2.5`, `scipy>=1.11` (scipy odpada w fazie D) |
| P0.2 | `BASE_DIR` nieprzeprowadzone — gra działa tylko z CWD == katalog projektu | classes/Sprites.py:10-19 (`./sprites/...`), entities/Item.py:9 (`./img/font.png`), classes/Pause.py:13 (`./img/title_screen.png`), classes/Level.py:27 (fallback `./levels`; main.py:21 nie przekazuje `base_dir` do `Level`), entities/Mario.py:16 (`Sprites()` w chwili importu) | przeprowadzić `base_dir` przez `Sprites`/`Item`/`Pause`/`Level`; refaktor jest już w połowie (10 niezacommitowanych plików) — dokończyć i zacommitować |

### P1 — poprawność (logika gry)

**P1.1 Zamrożenie ekranu na końcu poziomu (zweryfikowano).**
`classes/Level.py:87-102` — `drawLevel` iteruje
`for x in range(0 - int(camera.pos.x + 1), 20 - int(camera.pos.x - 1))`.
Dla `camera.pos.x <= -40` zakres sięga x=60, a grid ma 60 kolumn
(0..59) → `IndexError` cicho połknięty przez `except IndexError: return`
(wiersze 101-102) → poziom nie jest rysowany i `updateEntities` nie jest
wywoływane — ekran zamrożony. Łańcuch: `Collider.rightLevelBorderReached`
(classes/Collider.py:65-69) przycina Mario do kolumny 59;
`Camera.move` (classes/Camera.py:13-14) blokuje kamerę na
`pos.x = -40` dla `xPosFloat >= 50`.
Poprawka: przyciąć x do gridu (`min(x, levelLength-1)`), okno kamery z
`levelLength` (P1.2), a właściwy „koniec” to flaga (faza B).

**P1.2 Kamera hardkodowana pod poziomy 60-kafelowe.**
`classes/Camera.py:13-14` — `if 10 < xPosFloat < 50`. Każda inna
długość poziomu psuje podążanie kamery.
Poprawka: okno wyliczane z `levelLength` i `pos.x` przycinane do
`[-(levelLength-20), 0]`.

**P1.3 `EntityCollider.determineSide` — błędne współrzędne (zweryfikowano).**
`classes/EntityCollider.py:16-18` —
`rect2.collidepoint((rect1.midleft[0] / 2, rect1.midleft[1] / 2))`:
współrzędne świata (piksele) dzielone przez 2 przed testem punktu,
więc punkt wypada ~2× dalej niż zamierzony → `isTop` w praktyce
arbitralny (stomp działa tylko dzięki fallbackowi `vel.y > 0`,
wiersze 21-22).
Poprawka: stronę określaj po pozycji/przeniknięciu (np. pionowe
nakładanie < progu i dolna krawędź encji poniżej górnej krawędzi
platformy → „na wierzchu”), nie po dzieleniu współrzędnych.

**P1.4 Niekonsekwentna konwencja współrzędnych encji (zweryfikowano
testem spawnów).**

- JSON poziomów: moby (Goomba/Koopa) jako `[wiersz, kolumna]`
  (np. Koopa `[12, 25]` = wiersz 12, kolumna 25 — we wszystkich
  wpisach Koopa pierwszy element = 12 = wiersz), przedmioty
  (Coin/CoinBox/…) jako `[kolumna, wiersz]`.
- `Level.loadEntities` (classes/Level.py:35-44) rozpakowuje wszystko
  jako `for x, y in ...`.
- `super().__init__`: Goomba.py:11 → `EntityBase(y, x-1)`,
  Koopa.py:13 → `EntityBase(y-1, x)`, Mushroom.py:11 →
  `EntityBase(y, x-1)`, a Coin/CoinBox/CoinBrick/RandomBox — proste
  `(x, y)`.
- Spawny zmierzone (Level1-1): Goomba `[12,15]` → kolumna 15, wiersz 11
  (jeden wiersz nad ziemią — pada, OK); Koopa `[12,25]` → kolumna 24,
  wiersz 12 (jedna kolumna w lewo — OK); RandomBox `(4,3)` →
  grzyb kolumna 4, wiersz 1 (2 wiersze nad skrzynką — dzięki
  „podwójnemu zamianie” w RandomBox.py:28 + Mushroom.py:11).

Działa wszystko, ale tylko dzięki wzajemnemu skompensowaniu —
dodanie nowego poziomu lub encji to pewna usterka.
Poprawka: ujednolicić `(kolumna, wiersz)` w JSON i `(x, y)` w
konstruktorach; usunąć offsety z `super()`; skorygować JSON-y poziomów.

**P1.5 Kolejność aktualizacji i wejście w `Mario.update`.**
`entities/Mario.py:62-70` — wejście odczytywane na końcu (wiersz 70),
po fizyce → opóźnienie sterowania o klatkę. Dodatkowo brak
zmiennej wysokości skoku: `traits/jump.py:9-22` — stała wysokość,
bez skrócenia po puszczeniu klawisza.
Poprawka: wejście jako pierwsze; skok zmienny (po puszczeniu, gdy
`vel.y < 0`, prędkość pionowa pomniejszana, np. ×0.4).

**P1.6 Modyfikacja `entityList` podczas iteracji.**
`entities/Mario.py:78-90` — `self.levelObj.entityList.remove(item)`
wewnątrz `for ent in self.levelObj.entityList` → pomijanie encji, gdy
kilka kolizji w jednej klatce (np. 2 monety).
Poprawka: iterować `list(self.entityList)` (jak robi
`Level.updateEntities`, classes/Level.py:82) albo mark-and-sweep.

**P1.7 Level1-2.json nie ma `entities` (zweryfikowano).**
Brak bloku `"entities"`; `Level.loadEntities` (classes/Level.py:36-44)
łapie `(KeyError, TypeError)` i `pass` → poziom ładowany cicho
z 0 encjami.
Poprawka: uzupełnić poziom (faza C) LUB wywalić głośny błąd
(jasny komunikat) — `pass` wywalić.

**P1.8 Brak pętli gry.**
Brak zwycięstwa (brak flagi), brak żyć, timer liczy **w górę**
(classes/Dashboard.py:31-34 — bez limitu czasu), brak przejścia do
następnego poziomu. Jedyny „wyjście”: pauza → BACK TO MENU.
Poprawka: faza B.

**P1.9 Moby schodzą z krawędzi do otchłani (latent).**
`traits/leftrightwalk.py:14-24` — zwrot tylko gdy `vel.x == 0`
(najechanie na ścianę); brak detekcji urwiska. Level1-1 nie ma
jamek (pełne podłoże), więc błąd się nie ujawnia; śmierć przez
upadek jest już zaimplementowana w `Collider.checkY`
(classes/Collider.py:40-45).
Poprawka: faza C (detekcja urwisku).

**P1.10 Martwa gałąź w `_onCollisionWithMob`.**
`entities/Mario.py:111-116` — warunek `isTop and mob.alive and not
mob.active` jest nieosiągalny: poprzednia gałąź (106-110) łapie
wszystkie `mob.alive` (`mob.alive or mob.bouncing`).
Poprawka: przeorganizować warunki (stomp Goomba = śmierć, stomp Koopa
= muszla, kopnięcie muszli) z czytelnymi predykatami.

### P2 — jakość kodu / architektura

| # | Problem | Gdzie | Poprawka |
|---|---------|-------|----------|
| P2.1 | Gołe `except Exception:` połykające wszystko | classes/Collider.py:17-18, 40-45; classes/Level.py:43-44, 101-102, 111-112, 133-134, 145-146; entities/EntityBase.py:29-30 | zwężone typy (`IndexError`/`KeyError`), logowanie (`logging`), głośny błąd przy błędzie poziomu |
| P2.2 | `killEntity` porównuje **nazwy klas jako string** (`"Goomba"`, `"Koopa"`) | entities/Mario.py:141-142 | `isinstance` po przeorganizowaniu (P1.10) |
| P2.3 | Niezgodny klucz traitu: `Collider` szuka `"JumpTrait"`, w słowniku Mario jest `"jumpTrait"` → `JumpTrait.reset()` **nigdy się nie wywołuje** | classes/Collider.py:57-58 vs entities/Mario.py:48 | ujednolicić klucz (obserwowane: brak skutków poza estetyką, bo reset pokrywa się z ruchem) |
| P2.4 | `Item` dziedziczy po `Dashboard` (złe relacje) | entities/Item.py:7-9 | `Item(EntityBase)` + własny `drawText` lub przekazywany `dashboard` |
| P2.5 | `Dashboard.drawText` buduje font surface **na każdy znak, na każdą klatkę** (HUD 4×60 fps) | classes/Dashboard.py:36-41 | cache powierzchni (font + rozmiar → surface) |
| P2.6 | `Level.drawLevel` łączy render i symulację — wewnątrz pętli rysowania wywołuje `updateEntities` | classes/Level.py:87-100 | `update()` i `draw()` osobno; `drawLevel` nie zmienia stanu |
| P2.7 | Moby nie kolizują między sobą — jedyna kolizja encji to `EntityCollider` z `mario` | entities/Mario.py:78-90 | faza C (opcjonalnie: mob-mob) |
| P2.8 | `Mario.gameOver` — blokuje pętlę na 500 klatek bez wejścia; `mario_dead` nie jest nigdzie używane | entities/Mario.py:152-173, sprites/Mario.json | faza B (życia) + D6 (nazwy); animacja śmierci — C |
| P2.9 | `Pause` buduje **pełnoekranowe rozmycie w konstruktorze** (droga operacja, wykonywana przy każdym `Pause(...)`) oraz `createBackgroundBlur` nigdy nie jest wywoływane; ESC nie zamyka pauzy | classes/Pause.py:14, 58-59, 39-56 | blur tylko po wejściu w pauzę, ESC/close zamyka, usunąć martwe API |
| P2.10 | Nazewnictwo: `Level.level` (grid kafli — mylone z samym poziomem), `alive is None` jako sentinel usuwania, `CoinBox.__init__` `self.vel = 1` (int, nie wektor) | classes/Level.py:21, 84; entities/CoinBox.py | `tiles`/`grid`; flaga `deleted` wektor `Vector2` |

### P3 — repozytorium / narzędzia

| # | Problem | Gdzie | Poprawka |
|---|---------|-------|----------|
| P3.1 | `compile.py` używa `distutils` (usunięty w Python 3.12) i py2exe (Windows-only, nie wspiera 3.14) | compile.py:1-40 | usunąć, albo zastąpić PyInstaller (cross-platform) |
| P3.2 | README opiszane pod starą wersję (pygame 2.0, brak info o BASE_DIR, bez instrukcji testów) | README.md | odświeżyć w fazie E |
| P3.3 | 10 plików z niezacommitowanymi zmianami (refaktor BASE_DIR w połowie) | git status | dokończyć + commit przed fazą B |
| P3.4 | Brak testów, lintera, CI | repo | faza E |
| P3.5 | Nieużywane zasoby: `mario_dead`, `mario_break`, `mario_big_break` (sprites/Mario.json), `img/yoshis.png` (528×691), prawdopodobnie nadmiar klatek w `img/Items.png` (576×336, użyte: moneta-grzbiet, grzyb) | sprites/*.json, img/ | audyt: albo podpiąć (faza C), albo oznaczyć |

---

## 5. Fazy rozwoju

### Faza A — stabilizacja (błędy P0 + P1, bez nowych funkcji)

- **A1** `requirements.txt` → `pygame-ce>=2.5`, `scipy>=1.11` (scipy zostaje do fazy D;
  import `pygame` bez zmian — pygame-ce jest drop-in).
- **A2** dokończenie refaktora `BASE_DIR`: przeprowadzić `base_dir` przez
  `Sprites` (classes/Sprites.py:10-19), `Item` (entities/Item.py:9), `Pause`
  (classes/Pause.py:13), `Level` (classes/Level.py:27, main.py:21) i import
  `Sprites()` w `entities/Mario.py:16` → `Mario` dostaje `base_dir` w
  konstruktorze. **Commit przed fazą B.**
- **A3** `Level.drawLevel`: przyciąć `x` do `levelLength-1` (P1.1);
  `Camera`: okno wyliczane z `levelLength` (P1.2).
- **A4** przebudowa `EntityCollider.determineSide` (P1.3): porównanie krawędzi
  i głębokości pionowego przeniknięcia, bez dzielenia współrzędnych.
- **A5** ujednolicenie konwencji `(kolumna, wiersz)` w JSON i `(x, y)` w
  konstruktorach encji (P1.4); aktualizacja Level1-1.json i testy spawnów.
- **A6** `Mario.update`: wejście jako pierwsze (P1.5); iteracja po
  `list(self.entityList)` (P1.6).
- **A7** zmienna wysokość skoku (P1.5): po puszczeniu klawisza, gdy `vel.y<0`,
  prędkość pionowa ×0.4.
- **A8** `loadEntities`: głośny błąd dla brakującego/płaskiego `entities`
  (P1.7, P2.1) — `pass` znika.
- **A9** `Collider`: klucz traitu `"jumpTrait"` (P2.3); przeorganizowanie
  `_onCollisionWithMob` (P1.10) + `isinstance` zamiast stringów (P2.2).
- **A10** `Collider.rightLevelBorderReached` blokuje Mario przy krawędzi dopiero
  gdy jest flaga (faza B) — do tego czasu zachowanie z P1.1 (przecięcie drawLevel)
  jest akceptowalne.

### Faza B — pełna pętla gry

- **B1** koniec poziomu = **flaga** (asset: brak w `img/` — dorysować w stylu
  oryginału albo użyć kafelka z `Tiles.png`): dotknięcie flagi → sekwencja
  „zwycięstwo poziomu” (Mario zjeżdża, chowa się, czas zatrzymany).
- **B2** życia: 3 życia, screen „GAME OVER” → menu; śmierć przez upadek
  (istniejąca, `Collider.checkY`) i trafienie mobem → -1 życie + respawn w
  punkcie startowym.
- **B3** odliczanie czasu: 300 „jednostek” (1 jednostka ≈ 1/4 s, jak w oryginale)
  przez `Dashboard` (klasyk: HUD `TIME 300`); czas == 0 → śmierć.
- **B4** 100 monet → +1 życie (klasyczne reguły; licznik w `Level`/`Dashboard`).
- **B5** postęp: `Level1-1` → `Level1-2` → (1-3, 1-4 w fazie C); stan
  przechowywania w `settings.json` (ostatni ukończony poziom) — plik już
  gitignored, czyta/pisze `Menu` (classes/Menu.py:45, 259, 269).
- **B6** animacja śmierci `mario_dead` (sprites/Mario.json) zamiast 500-klatkowej
  blokowej pętli (P2.8).

### Faza C — zawartość

- **C1** uzupełnienie `Level1-2.json` (bloku `entities` w ogóle brak — P1.7)
  i nowe poziomy `Level1-3.json`, `Level1-4.json` (wzorować na 1-1; przestrzegać
  konwencji z §3: podłoże `y:[14,16]`, moby `[wiersz,kolumna]` → po A5
  ujednolicone).
- **C2** fire flower + **fire Mario** — ⚠️ wymaga audytu assetów:
  `sprites/Characters.json` ma tylko małego/dużego Mario (bez wersji z
  ogniem); klatki w `img/Items.png` do potwierdzenia. Jeśli brak → dorysować
  (3 klatki chodu + skok) przed startem C2; bez tego faza C2 czeka.
- **C3** 1-UP (zielony grzyb) w `RandomBox` — `img/Items.png` ma klatkę 1-UP
  do potwierdzenia.
- **C4** Yoshi — `img/yoshis.png` (528×691) nieużywany; wymagana mapa klatek
  (przebieg, jeżdżenie, chwytanie) + `Yoshi.py` (encja + stan „przyciągnięty”).
- **C5** łamanie cegieł (mały Mario: `coinBrick` → moneta; duży: kruszy)
  — `sprites/Tiles.png` ma klatki `brick-break` do potwierdzenia.
- **C6** mob–mob kolizje + detekcja urwisku dla mobów (P1.9, P2.7): zwrot przy
  braku kafela pod stopą.
- **C7** opcjonalnie: dodatkowe `CoinBox`/`RandomBox` w nowych poziomach,
  ukryte 1-UP w cegle (klasyk 1-1).

### Faza D — dopracowanie

- **D1** pozbycie się `scipy` (zależność tylko dla `GaussianBlur`):
  pygame-ce ma `pygame.transform.smoothscale`/`rotozoom` — prosty box-blur
  w 2 passach, albo cache rozmycia tła. `requirements.txt` → tylko pygame-ce.
- **D2** cache fontu w `Dashboard` (P2.5).
- **D3** głośność: suwak 0–100 w menu → zapis do `settings.json` (mechanizm
  pliku istnieje w `Menu`, brakuje opcji głośności).
- **D4** fullscreen / skalowanie (640×480 ×1/×2, `pygame.display.set_mode`).
- **D5** pauza: ESC zamyka, blur tylko po otwarciu, usunięcie `createBackgroundBlur`
  (P2.9).
- **D6** porządki nazw: `Level.level` → `grid`, sentinel `alive is None` →
  flaga `deleted`, `CoinBox.vel` → `Vector2` (P2.10).
- **D7** refaktor `Level.drawLevel` → `update()` + `draw()` osobno (P2.6).

### Faza E — infrastruktura

- **E1** suite testów pytest, headless (z istniejących skryptów
  `/tmp/opencode/`: smoke, camera, spawns, collider) — szczegóły w §7.
- **E2** GitHub Actions: Python 3.11/3.12/3.13 matrix, instalacja z
  `requirements.txt`, `pytest` headless.
- **E3** `ruff` + `.editorconfig` (bez CI nie ma kompromisu).
- **E4** README: odświeżenie (pygame-ce, instalacja, struktura, sterowanie,
  jak dodać poziom).
- **E5** `compile.py`: usunąć lub podmienić na PyInstaller (P3.1).
- **E6** (reguła) commit każdej fazy; faza A — przed B (zob. ryzyka).

---

## 6. Tabela zadań (kolejność wykonania)

| ID | Zadanie | Główne pliki | Trudność |
|----|---------|--------------|----------|
| A1 | requirements: pygame-ce, scipy (min) | requirements.txt | S |
| A2 | dokończenie BASE_DIR + commit | main.py, classes/Sprites.py, entities/Item.py, classes/Pause.py, classes/Level.py, entities/Mario.py | M |
| A3 | drawLevel clamp + kamera z levelLength | classes/Level.py, classes/Camera.py | S |
| A4 | determineSide bez /2 | classes/EntityCollider.py | M |
| A5 | ujednolicenie (kolumna, wiersz) | classes/Level.py, entities/*.py, levels/*.json | M |
| A6 | input-first + list() iteracji | entities/Mario.py | S |
| A7 | zmienny skok | traits/jump.py, entities/Mario.py | S |
| A8 | głośny błąd loadEntities | classes/Level.py | S |
| A9 | klucz traitu + reorg kolizji mobów | classes/Collider.py, entities/Mario.py | M |
| A10 | (zastrzeżenie) blokada krawędzi → faza B | classes/Collider.py | S |
| B1 | flaga + zwycięstwo poziomu | entities/Flag.py (nowy), classes/Level.py, entities/Mario.py, img/ (asset) | L |
| B2 | 3 życia + game over | entities/Mario.py, classes/Dashboard.py, main.py | M |
| B3 | timer 300 w dół | classes/Dashboard.py, main.py | S |
| B4 | 100 monet → +1 życie | classes/Level.py, entities/Coin.py | S |
| B5 | postęp poziomów + zapis | classes/Menu.py, main.py, settings.json | M |
| B6 | animacja śmierci mario_dead | entities/Mario.py, sprites/Mario.json | S |
| C1 | Level1-2 + poziomy 1-3/1-4 | levels/Level1-*.json | M |
| C2 | fire flower + fire Mario | ⚠️ assety (Characters.json/Items.png), entities/Mushroom.py, entities/Mario.py, entities/FireMario.py (nowy) | L |
| C3 | 1-UP w RandomBox | entities/RandomBox.py, entities/OneUp.py (nowy), img/Items.png | S |
| C4 | Yoshi | img/yoshis.png (mapa klatek), entities/Yoshi.py (nowy), traits/ | L |
| C5 | łamanie cegieł | entities/CoinBrick.py, entities/Mario.py, sprites/Tiles.png | M |
| C6 | mob–mob + urwiska | traits/leftrightwalk.py, classes/EntityCollider.py | M |
| C7 | dodatkowe skrzynie (opcja) | levels/*.json | S |
| D1 | blur bez scipy | classes/GaussianBlur.py, requirements.txt | M |
| D2 | cache fontu Dashboard | classes/Dashboard.py | S |
| D3 | głośność 0–100 | classes/Menu.py, classes/Sound.py, settings.json | M |
| D4 | fullscreen/skalowanie | main.py | S |
| D5 | pauza: ESC + blur na żądanie | classes/Pause.py, classes/Input.py | S |
| D6 | porządki nazw (P2.10) | classes/Level.py, entities/EntityBase.py, entities/CoinBox.py | S |
| D7 | update/draw osobno | classes/Level.py, main.py | M |
| E1 | pytest headless | tests/*, conftest.py | M |
| E2 | GitHub Actions CI | .github/workflows/ci.yml | S |
| E3 | ruff + .editorconfig | pyproject.toml, .editorconfig | S |
| E4 | README | README.md | S |
| E5 | compile.py → PyInstaller/usuń | compile.py | S |

---

## 7. Strategia testów

- **Headless always**: `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`
  (setup w `conftest.py`); screen 640×480, `Dashboard` i `Sound` jako
  współdzielone fixtury.
- `tests/test_level.py` — ładowanie Level1-1 (długość 60, 37 encji),
  grid 15 wierszy; test głośnego błędu przy braku `entities` (A8);
  spawn: Goomba `[12,15]`→kolumna 15/wiersz 11, Koopa `[12,25]`→
  kolumna 24/wiersz 12, RandomBox `(4,3)`→grzyb kolumna 4/wiersz 1
  (wartości ze zweryfikowanego `spawn_test.py`).
- `tests/test_camera.py` — okno kamery dla długości 60 **i 90** (regresja
  P1.2); `drawLevel` dla `camera.pos.x <= -40` nie wyrzuca i nie przerywa
  (regresja P1.1).
- `tests/test_collider.py` — `checkY` przy upadku poza grid (gameOver),
  `determineSide` na krawędziach (regresja P1.3), klucz traitu (regresja
  P2.3).
- `tests/test_mario.py` — stomp Goomba, stomp Koopa → muszla, wejście
  jako pierwsze (P1.5), iteracja `list()` (P1.6), zmienny skok (A7).
- `tests/test_smoke.py` — 120 klatek `updateEntities` + `drawLevel`
  bez wyjątków (jak dotychczasowy `smoke_test.py`).
- CI (E2) uruchamia cały suite na każdym PR.

---

## 8. Ryzyka i zastrzeżenia

- **Fire Mario bez assetów** — `sprites/Characters.json` nie zawiera
  wersji z ogniem; C2 czeka na dorysowanie klatek (szac. 4 klatki:
  idle/run×3/jump) lub decyzję o pominięciu. Bez tego faza C2 nie startuje.
- **Yoshi wymaga mapy klatek** — `img/yoshis.png` (528×691) to surowy sheet
  bez metadanych; przed C4 trzeba ustalić layout (wiersze × kolumny × rozmiar
  klatki) i stan animacji.
- **Konwencja wierszy gridu** — podłoże w JSON `y:[14,16]`, a kafle
  kolizji generowane z offsetem `(y-1)*32` (classes/Level.py:52-61), więc
  podłoże „w praktyce” zajmuje wiersze 13-14. Należy to udokumentować
  **przed** pisanem nowych poziomów (C1), inaczej każdy nowy poziom
  odziedziczy offset.
- **Niedokończony refaktor BASE_DIR** — 10 niezacommitowanych plików;
  dokończenie + commit to warunek wejściowy fazy B (A2), bo B zmienia
  `Menu`/`Level`/`main.py` i nakładanie się zmian zwiększy koszt
  merge.
- **pygame → pygame-ce** — drop-in (ten sam moduł `pygame`), ale testy
  powinny działać na pygame-ce (nie na vanilla pygame 2.x).
- **settings.json jest gitignored** — nie ma pliku w repo; testy i CI
  muszą go tworzyć (fixture), inaczej `Menu` wywali przy starcie.
- **Zakres** — funkcje na skalę SMB3 (wody, rury z wiatrem, power-upy
  łańcuchowe, world map) są poza zakresem assetów; nie planowane.

---

*Utworzono: 2026-10-27. Status: PLAN MODE — żaden plik źródłowy nie został
zmodyfikowany; jedyny efekt tego przeglądu to ten dokument.*
