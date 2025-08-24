# Quest Tracking System

## 🎯 Účel systému
- Presné sledovanie progressu v hre
- Prevencia spoilerov
- Kontextovo relevantné odpovede
- Story-aware responses

## 📊 Štruktúra quest záznamu

### Základné informácie
```yaml
quest_id: string           # Unikátny identifikátor questu
title: string             # Názov questu
type: enum                # main_story, side_quest, gig, etc.
phase: enum               # not_started, active, completed, failed
act: number              # 1, 2, 3 (pre main story)
location: string         # District/área
fixer: string            # Zadávateľ (ak existuje)
```

### Stavy questu
```yaml
states:
  - state_id: string     # Unikátny ID stavu
    description: string   # Popis stavu
    completed: boolean   # Či je stav dokončený
    requirements:        # Podmienky pre tento stav
      - condition: string
    next_states:        # Možné následujúce stavy
      - state_id: string
    triggers:           # Čo spúšťa tento stav
      - trigger: string
    variables:          # Sledované premenné
      - var_name: value
```

### Dialógové stromy
```yaml
dialogues:
  - dialogue_id: string
    speaker: string
    conditions:         # Kedy sa dialóg zobrazí
      - condition: string
    choices:           # Možné odpovede
      - choice_id: string
        text: string
        requirements:  # Podmienky pre možnosť
        consequences: # Čo spôsobí táto voľba
    next_dialogue:    # Následujúci dialóg
      - condition: string
        dialogue_id: string
```

### Dopady rozhodnutí
```yaml
choices:
  - choice_id: string
    impact:
      immediate:      # Okamžité následky
        - effect: string
      delayed:       # Neskoršie následky
        - effect: string
      relationship:  # Vplyv na vzťahy
        - character: string
          change: number
```

## 🔄 Live State Tracking

### CET (Cyber Engine Tweaks) Integrácia
```lua
-- Príklad sledovaných premenných
Game.GetQuestsSystem()
Game.GetPlayer()
Game.GetWorkspotSystem()
Game.GetTimeSystem()
```

### State Monitoring
- Quest stavy
- Inventory
- Vzťahy s NPC
- Lokácia
- In-game čas
- Aktívne efekty
- Vybavenie

### OCR Integration
- Rozpoznávanie dialógov
- Quest notifikácie
- UI elementy
- Subtitles

## 🚫 Spoiler Prevention

### Úrovne informácií
1. Known        # Už objavené/dokončené
2. Available    # Dostupné, ale nezačaté
3. Hinted      # Náznaky existencie
4. Hidden      # Zatiaľ neodkryté

### Pravidlá pre odpovede
1. Neodkazovať na budúce udalosti
2. Nezmieniť následky rozhodnutí
3. Nenaznačovať existenciu skrytého obsahu
4. Držať sa aktuálneho kontextu

## 📈 Story Progression Tracking

### Main Story Progress
```yaml
act: number             # Aktuálny act
main_quest: string     # Aktuálny hlavný quest
branch: string         # Aktívna story branch
completion: number     # Celkový progress (%)
```

### Side Content Progress
```yaml
side_quests_completed: number
gigs_completed: number
ncpd_completed: number
cyberpsychos_found: number
relationships:
  - character: string
    status: string
    progress: number
```

## 🔗 Quest Dependencies

### Prerekvizity
- Level requirements
- Story progression
- Character relationships
- Previous choices
- Item possession
- Skills/perks

### Blokátory
- Mutually exclusive quests
- Časové obmedzenia
- Location access
- Faction reputation
- Failed prerequisites
