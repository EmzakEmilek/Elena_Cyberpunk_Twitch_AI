# RAG Knowledge Base - Card Templates & Structure

## Card Categories and Templates

### 1️⃣ Quest Cards
```yaml
template: quest_card
fields:
  title: string                     # Quest name
  category: enum                    # main_story, side_quest, gig
  quest_id: string                 # Unique identifier
  act: number                      # Game act/phase
  phase_requirements:              # What must be true for this quest
    story_phase: string
    player_level: number
    street_cred: number
    previous_quests: [string]
  content:
    summary: string               # Brief overview
    key_events: [string]         # Major events
    critical_choices: [object]    # Player decisions
    progression_flags: object     # Story/world state changes
    objectives: [object]         # Detailed objectives
  dialogue_trees: [object]       # All possible conversations
  world_state_changes: [object]  # What changes after quest
  rewards: object               # Items, money, exp
  quest_flags: object          # Technical quest states
```

### 2️⃣ Character Cards
```yaml
template: character_card
fields:
  title: string                  # Character name
  category: enum                # major, supporting, vendor
  char_id: string              # Unique identifier
  content:
    summary: string            # Brief bio
    background: object        # History
    personality: object       # Traits, behaviors
    relationships: object     # Links to other characters
  story_relevance: object    # Role in plot
  quest_appearances: [string] # Related quests
  current_status: object     # Alive/dead, location
  technical_details: object  # Game-specific info
```

### 3️⃣ Location Cards
```yaml
template: location_card
fields:
  title: string                # Location name
  category: enum              # district, landmark, building
  location_id: string        # Unique identifier
  content:
    summary: string         # Brief description
    characteristics: object # Physical details
    notable_locations: [object] # Sub-locations
    controlling_factions: object # Who controls it
  activities: object       # What happens here
  quest_relevance: [string] # Related quests
  accessibility: object   # When/how accessible
```

### 4️⃣ Faction Cards
```yaml
template: faction_card
fields:
  title: string              # Faction name
  category: enum            # corp, gang, nomad
  faction_id: string       # Unique identifier
  content:
    summary: string       # Brief overview
    structure: object    # Organization details
    territory: object   # Where they operate
    resources: object  # What they control
  relationships: object # With other factions
  quest_relevance: [string] # Related quests
  current_status: object # Power/influence
```

### 5️⃣ Technology Cards
```yaml
template: technology_card
fields:
  title: string            # Tech name
  category: enum          # cyberware, weapon, vehicle
  tech_id: string        # Unique identifier
  content:
    summary: string     # Brief description
    specifications: object # Technical details
    variants: [object] # Different versions
    availability: object # Where to get it
  gameplay_impact: object # How it affects play
  quest_relevance: [string] # Related quests
```

## 📁 Directory Structure

/lore
  /quests
    /main_story
    /side_quests
    /gigs
    /phantom_liberty
    _index.yaml         # Quest relationships
    _templates.yaml     # Quest templates
  
  /characters
    /major
    /supporting
    /vendors
    _index.yaml
    _templates.yaml
  
  /locations
    /districts
    /landmarks
    /buildings
    _index.yaml
    _templates.yaml
  
  /factions
    /corporations
    /gangs
    /other_groups
    _index.yaml
    _templates.yaml
  
  /technology
    /cyberware
    /weapons
    /vehicles
    _index.yaml
    _templates.yaml

## 🔄 Cross-References

Každá karta obsahuje:
1. Unique ID pre referencie
2. Related_cards pole
3. Quest_relevance pre story kontext
4. Current_status pre časovú relevantnosť

## 🔍 Search Optimization

Keywords pre každú kartu:
1. Alternatívne mená/názvy
2. Súvisiace koncepty
3. Časté player dotazy
4. Quest/story fázy

## 📊 Metadata

Každá karta obsahuje:
1. Version control
2. Last updated
3. Content source
4. Spoiler rating
5. Importance rating
