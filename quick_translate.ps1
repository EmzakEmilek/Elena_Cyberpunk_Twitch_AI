# Elena Lore - Quick Translation Script
param(
    [string]$LorePath = "c:\Users\echov\Desktop\Kódenie\Elena\lore",
    [int]$MaxFiles = 20
)

$ProcessedCount = 0
$TranslationMap = @{
    "Advanced technology" = "Pokročilá technológia"
    "Corporate security" = "Korporátna bezpečnosť"
    "Street gang" = "Pouličná gang"
    "Underground club" = "Underground klub"
    "Weapon system" = "Zbraňový systém"
    "Neural implant" = "Neurálny implantát"
    "Combat zone" = "Bojová zóna"
    "dangerous" = "nebezpečný"
    "powerful" = "mocný"
    "advanced" = "pokročilý"
    "illegal" = "nelegálny"
    "expensive" = "drahý"
    "enhance" = "vylepšiť"
    "improve" = "zlepšiť"
    "increase" = "zvýšiť"
    "protect" = "chrániť"
    "attack" = "útočiť"
    "defend" = "brániť"
}

function Test-IsSlovak {
    param([string]$Content)
    $SlovakChars = $Content -match '[áäčďéíĺľňóôöŕšťúýž]'
    $EnglishWords = $Content -match '\b(the|and|of|to|in|for|with|Advanced|System|Combat|Weapon)\b'
    return ($SlovakChars -and !$EnglishWords)
}

function Invoke-QuickTranslation {
    param([string]$Content)
    $Result = $Content
    foreach ($EN in $TranslationMap.Keys) {
        $SK = $TranslationMap[$EN]
        $Result = $Result -replace "\b$EN\b", $SK
    }
    return $Result
}

Write-Host "🚀 ELENA QUICK TRANSLATION STARTED" -ForegroundColor Cyan
$Files = Get-ChildItem -Path $LorePath -Recurse -Filter "*.yaml" | Select-Object -First $MaxFiles

foreach ($File in $Files) {
    try {
        $Content = Get-Content $File.FullName -Raw -Encoding UTF8
        
        if (Test-IsSlovak $Content) {
            Write-Host "✅ SKIP: $($File.Name) (already Slovak)" -ForegroundColor Green
            continue
        }
        
        if ($Content -match "translation_status.*automated") {
            Write-Host "⏭️ SKIP: $($File.Name) (already processed)" -ForegroundColor Yellow
            continue
        }
        
        # Backup
        $BackupPath = $File.FullName + ".backup"
        Copy-Item $File.FullName $BackupPath -Force
        
        # Translate
        $Translated = Invoke-QuickTranslation $Content
        
        # Add metadata
        $Updated = $Translated + "`n`n# Automated translation - $((Get-Date).ToString('yyyy-MM-dd HH:mm'))"
        
        # Save
        Set-Content -Path $File.FullName -Value $Updated -Encoding UTF8
        
        Write-Host "🔄 PROCESSED: $($File.Name)" -ForegroundColor Cyan
        $ProcessedCount++
        
    } catch {
        Write-Host "❌ ERROR: $($File.Name) - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n✨ COMPLETED: Processed $ProcessedCount files" -ForegroundColor Green
