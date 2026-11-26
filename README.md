# Z-Pet

A pocket pixel-art virtual pet RPG built for the **M5Stack Cardputer Zero** (`320×170` SPI display) with full PC preview support. Raise one of 5 unique starter companions, customize their coat color and name, train their battle stats, play arcade mini-games, and unlock **35 Baby, Teen, and Adult evolutions** shaped by how you care for them.

![Z-Pet Screenshot](assets/images/screenshot01.png)

---

## Quick Controls

Z-Pet uses unified directional controls across menus, mini-games, and the bedroom dock—supporting both standard arrow keys and the Cardputer Zero's left-hand cluster:

| Action | Keys |
| :--- | :--- |
| **Up / Down** | `↑` / `↓` or `F` / `X` |
| **Left / Right** | `←` / `→` or `Z` / `C` |
| **Select / Confirm / Action** | `Enter` or `Space` |
| **Back / Save & Menu / Quit** | `Esc` or `Q` |
| **Open The Guide** *(from Status screen)* | `G` |
| **Switch Guide Tabs** | `←` / `→`, `Tab`, or `1` / `2` / `3` |
| **Take `320×170` Screenshot** | `0` *(Cardputer Zero)* or `F12` *(PC)* |

> **Tip when naming a New Pet:** While the **Name** field is selected, `F`, `X`, `Z`, and `C` type letters normally—use the physical arrow keys or `Tab` to switch rows. Leave the name blank and press `Enter` to keep the starter's default name.

---

## Understanding the Screen & HUD

### Top Status Bar
* **Top-Left (`NAME Lv# B:#`):** Your pet's name, current **Level** (`Lv1`–`Lv30`), and **Bond** (`B:0`–`999`).
* **Top-Right (`Clock + Status`):** Real-time clock (`12h` or `24h` in Settings) followed by your pet's live status badge:
  * **`OK`** — Awake and doing fine.
  * **`ZZZ`** — Tucked into bed and recovering Energy.
  * **`MESSx#`** — Floor messes need cleaning.
  * **`FAINT`** — Pet collapsed from extreme neglect (press `Enter` to hatch a new egg).

### Care Bars (Top Row)
Each bar fills from `0%` to `100%` and shifts color by urgency (**Green** ≥ 60%, **Yellow** 30–59%, **Red** below 30%):

| Label | Meaning | How to Restore |
| :---: | :--- | :--- |
| **`HG`** | **Hunger** — How full your pet is. Reaching `0%` causes your pet to faint. | Feed a **Meal** (Apple) or **Treat** (Star). |
| **`HP`** | **Happiness** — Your pet's mood (not Hit Points). Low mood affects care quality. | Play **Star Catch**, give a **Treat**, or **Hug**. |
| **`EN`** | **Energy** — Stamina used for playing and training drills (needs ≥ 15%). | Put your pet to **Bed** (Moon icon). |
| **`CL`** | **Cleanliness** — Drops over time and whenever floor messes appear. | Use **Clean** (Bubbles icon). |

### Bottom Action Dock (8 Icons)
Slide across the dock with **`←` / `→`** (`Z` / `C`) and press **`Enter` / `Space`** to trigger the highlighted icon. A floating tooltip names the selected icon, and a **pulsing red dot** flags any stat that needs attention:

| Icon | Action | What It Does |
| :--- | :--- | :--- |
| **Apple** | **Meal** | Restores `+25` Hunger (`+29` for Bold pets), `+1` Bond, and awards XP. |
| **Golden Star** | **Treat** | Restores `+10` Hunger & `+14` Happiness, builds Bond, and awards XP. |
| **Striped Ball** | **Play** | Launches the 20-second **Star Catch** mini-game. |
| **Dumbbell** | **Train** | Opens **Teach** timing drills to permanently raise battle stats. |
| **Soap Bubbles** | **Clean** | Sweeps away floor messes, restores Cleanliness to `100%`, and awards XP. |
| **Moon / Sun** | **Bed / Wake** | Walks your pet to bed, tucks them under the covers, and dims the floor lamp. Recharges Energy at `1.25%/min` (~80 min for a full 0→100% rest). Swaps to a **Sun** icon while asleep. |
| **Heart** | **Hug** | Gives pets & affection (`+6` Happiness; `+3` Bond & XP every 6 seconds). |
| **Bar Chart** | **Status** | Opens the **Pet Status** profile (XP bar, battle stats, Care Path forecast, and `[G]` shortcut to **The Guide**). |

### Bedroom Details
* **Clock-Synced Window:** Displays **Dawn**, **Day** (drifting clouds), **Sunset**, or **Night** (twinkling stars & moon) synced to your real-time clock—or locked to any preset in **Settings**.
* **Standing Floor Lamp:** Glows warmly while awake and switches off automatically as the room dims for bedtime.
* **Shelf Trophy:** Turns gleaming gold and sparkles once you record a **Star Catch** high score.
* **Thought Bubbles:** Pop up beside your pet whenever Hunger, Cleanliness, Energy, or Happiness runs low.

---

## Status Screen & Battle Stats

Open the **Status** icon (Bar Chart) to check your pet's full RPG profile:

| Label | Meaning |
| :---: | :--- |
| **`ATK`** | **Attack** — Physical strike power (caps at `150`). |
| **`DEF`** | **Defense** — Damage reduction & guard strength (caps at `150`). |
| **`SPD`** | **Speed** — Turn order & agility (caps at `150`). |
| **`INT`** | **Intelligence** — Special skill & elemental power (caps at `150`). |
| **`XP`** | **Experience Points** — Earned from feeding, cleaning, hugging, Star Catch, and Teach drills up to **Lv. 30**. |
| **`BND`** | **Bond** — Affection score built through daily care, play, and training. |
| **`MST`** | **Care Mistakes** — Logged when Hunger, Happiness, or Cleanliness sits below `15%` (or 3+ messes sit uncleaned) for 30+ minutes. |
| **`TRN`** | **Daily Drills Remaining** — How many Teach sessions you have left today (`3/3` max, resets at midnight). |
| **`Skill`** | Your pet's active species signature ability. |

---

## Activities

### Star Catch (`Play`)
A 20-second arcade mini-game: move left and right to catch falling **Gold Stars** (`+1`) and rare **Pink Mega-Stars** (`+3`) while dodging **Storm Bolts** (`-1` & brief stun). Reaching a **5+ catch combo** adds `+1` bonus point per star, and scoring **12+ points** awards a permanent **`+1 SPD`** bonus!

### Teach Drills (`Train`)
Choose **ATK**, **DEF**, **SPD**, or **INT** and complete a 3-round timing-bar challenge. Hitting the center gold zone scores **PERFECT** (`+2` pts) and green scores **GOOD** (`+1` pt), granting permanent `+1` to `+3` stat gains, Bond, and XP. Capped at **3 sessions per calendar day** to keep progression balanced.

---

## Starters, Base Colors & Personalities

When starting a **New Pet**, choose from **5 Starter Species**, **7 Base Colors** (**Purple, Red, Yellow, White, Green, Pink, Blue**), and an optional custom name. Every starter line has a unique **Personality Trait** with active gameplay effects:

| Starter | Personality | Perks | Trade-off | Starting Stats (`A/D/S/I`) | Starter Skill |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Sparkkit** | **Hyper** | `+25%` Star Catch XP, `25%` faster walk | Hunger drains `15%` faster | `8 / 5 / 12 / 6` | *Static Pounce* |
| **Cinderpup** | **Bold** | `+25%` Teach XP, `+4` extra meal Hunger | Energy drains `10%` faster | `11 / 8 / 7 / 5` | *Ember Bite* |
| **Aquafin** | **Serene** | Energy drains `20%` slower, `+20%` sleep recovery | Clean drains `10%` faster | `5 / 8 / 7 / 11` | *Bubble Jet* |
| **Sproutowl** | **Gentle** | `+1` Bond on Hug/Treat, Hunger drains `20%` slower | Calm, slower walk | `6 / 11 / 6 / 8` | *Leaf Flurry* |
| **Cogbit** | **Curious** | `+25%` Care XP, `+1` bonus stat on Perfect drill | Happiness drains `15%` faster | `7 / 7 / 9 / 8` | *Logic Ping* |

---

## 3-Stage Care Evolution System (35 Species)

Pets level up from **Lv. 1 to Lv. 30**, evolving automatically when awake at **Lv. 10 (Teen)** and **Lv. 20 (Adult)**. How you raise your pet steers it into one of three distinct forms—and **Teens can still change care paths** before hitting Lv. 20:

* **Radiant Care:** Attentive, high-Bond care with very few mistakes (**Teen:** 0–1 MST & Bond 20+ · **Adult:** 0–2 MST & Bond 45+).
* **Trained Care:** Focused on daily Teach drills (**Teen:** 4+ drills & ≤ 2 MST · **Adult:** 9+ drills & ≤ 3 MST).
* **Wild Care:** Scrappy rogue path triggered by neglect or low Bond/drills (**Teen:** 3+ MST · **Adult:** 5+ MST). Wild forms aren't weak—they evolve into fierce, high-offense specialists!

| Starter (Baby, Lv. 1) | Teen Forms (Lv. 10 — Radiant / Trained / Wild) | Adult Forms (Lv. 20 — Radiant / Trained / Wild) |
| :--- | :--- | :--- |
| **Sparkkit** | Starlynx / Joltkat / Feralvolt | Aethercat / Voltlynx / Stormclaw |
| **Cinderpup** | Sunpup / Blazehound / Charfang | Solhound / Pyrofang / Ashmaw |
| **Aquafin** | Reefkin / Wavecrest / Murkfin | Coralshell / Tidedrake / Abyssfin |
| **Sproutowl** | Petalowl / Barkwing / Bramblet | Bloomwing / Ironbark / Thornbeak |
| **Cogbit** | Gildbot / Gearunit / Staticbit | Chronowing / Mechaforge / Glitchvex |

---

## The Guide & Settings

* **The Guide** *(Start-Up Menu or `[G]` in Status)*: Tracks all **35 species** permanently in `guide.json` across new playthroughs (showing silhouettes and unlock hints for undiscovered forms), plus quick-reference tabs for **Traits** and **Care** rules.
* **Settings** *(saved in `config.json`)*:
  * **Clock Format:** `12-Hour` or `24-Hour`.
  * **Window Sky:** `Auto` (real clock), `Dawn`, `Day`, `Sunset`, or `Night`.
  * **Game Speed:** `1x Normal`, `10x Fast`, or `60x Test`.

---

## Running & Installing

### On Cardputer Zero (1.9" Display via `/dev/fb_lcd`)
```bash
git clone [https://github.com/delos23/z-pet.git](https://github.com/delos23/z-pet.git) ~/z-pet
cd ~/z-pet
chmod +x deploy/install_launcher.sh deploy/run_zpet.sh
./deploy/install_launcher.sh
```
Launch **Z-Pet** directly from **APPLaunch**. Z-Pet renders natively to `/dev/fb_lcd` (even if HDMI is connected) and stores persistent data in `~/.config/z-pet/`:
* `save.json` — Active pet state & offline time tracking (up to 48 hours).
* `config.json` — User preferences from Settings.
* `guide.json` — Permanent 35-species discovery progress.

### On Windows / Linux PC (Development Preview)
```bash
pip install pygame-ce
python tools/generate_species_sprites.py
python main.py
```
Pass `--window` on Linux devices if you want a desktop preview window instead of `/dev/fb_lcd`.

---

## License
MIT License — Created by **Aaron Bumbarger** (`delos23`).