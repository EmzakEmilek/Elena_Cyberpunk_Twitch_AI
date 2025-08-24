# Test Mixed Content Impact

## Scenario 1: Pure Slovak Card
```yaml
name: "Braindance Technológia"
description: "Pokročilá technológia na nahrávanie a prehrávanie ľudských zážitkov"
```

**User query:** "Ako funguje braindance?"
**Expected response:** Pure Slovak explanation

## Scenario 2: Mixed Content Card  
```yaml
name: "Dark Matter"
description: "Underground technický klub, centrum hackerov"
physical_characteristics:
  exterior:
    - "Skrytý vstup" 
    - "Neon accents"
    - "Tech graffiti"
```

**User query:** "Ako vyzerá Dark Matter?"
**Likely response:** "Dark Matter je underground technický klub s neon accents a tech graffiti..."

## Scenario 3: Pure English Card
```yaml
name: "Targeting Systems"
description: "Advanced systems for improving weapon accuracy"
details: "System Components: Hardware, Software, Target tracking"
```

**User query:** "Čo sú targeting systémy?"
**Likely response:** "Targeting Systems sú advanced systems for improving weapon accuracy..."

## 🔴 PROBLEM IDENTIFICATION:
- **Response inconsistency** based on source material language
- **User confusion** from mixed terminology
- **Professional degradation** of Elena's persona
