# Elena Lore Database - Automated Translation & Standardization Script
# Author: GitHub Copilot
# Date: August 24, 2025
# Purpose: Bulk process 218 YAML files for Slovak translation and format standardization

param(
    [string]$LorePath = "c:\Users\echov\Desktop\Kódenie\Elena\lore",
    [switch]$DryRun = $false,
    [int]$BatchSize = 10
)

# Configuration
$LogFile = "c:\Users\echov\Desktop\Kódenie\Elena\logs\bulk_translation_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$BackupDir = "c:\Users\echov\Desktop\Kódenie\Elena\lore_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$ProcessedCount = 0
$ErrorCount = 0

# Create log directory if it doesn't exist
$LogDir = Split-Path $LogFile -Parent
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force
}

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry -ForegroundColor $(if($Level -eq "ERROR"){"Red"} elseif($Level -eq "WARN"){"Yellow"} else{"Green"})
    Add-Content -Path $LogFile -Value $LogEntry
}

# Translation dictionary for common terms
$TranslationMap = @{
    # Basic structure
    "name" = "name"
    "description" = "description"
    "details" = "details"
    "overview" = "overview"
    
    # Common English phrases to Slovak
    "Advanced technology" = "Pokročilá technológia"
    "Corporate security" = "Korporátna bezpečnosť"
    "Street gang" = "Pouličná gang"
    "Underground club" = "Underground klub"
    "Weapon system" = "Zbraňový systém"
    "Neural implant" = "Neurálny implantát"
    "Combat zone" = "Bojová zóna"
    "Night City" = "Night City"
    "Cyberware" = "Cyberware"
    "Netrunner" = "Netrunner"
    "Braindance" = "Braindance"
    "Corpo" = "Corpo"
    "Nomad" = "Nomád"
    "Street kid" = "Pouličné dieťa"
    
    # Common adjectives
    "dangerous" = "nebezpečný"
    "powerful" = "mocný"
    "advanced" = "pokročilý"
    "illegal" = "nelegálny"
    "expensive" = "drahý"
    "rare" = "vzácny"
    "common" = "bežný"
    "secure" = "bezpečný"
    "hidden" = "skrytý"
    "public" = "verejný"
    
    # Actions
    "enhance" = "vylepšiť"
    "improve" = "zlepšiť"
    "increase" = "zvýšiť"
    "decrease" = "znížiť"
    "protect" = "chrániť"
    "attack" = "útočiť"
    "defend" = "brániť"
    "hack" = "hacknúť"
    "upgrade" = "upgradovať"
    "install" = "nainštalovať"
}

# Function to detect if content is already in Slovak
function Test-IsSlovak {
    param([string]$Content)
    
    $SlovakChars = $Content -match '[áäčďéíĺľňóôöŕšťúýž]'
    $EnglishWords = $Content -match '\b(the|and|of|to|in|for|with|from|by|at|on|are|is|was|were|have|has|had|will|would|could|should)\b'
    
    if ($SlovakChars -and !$EnglishWords) {
        return $true  # Pure Slovak
    } elseif ($SlovakChars -and $EnglishWords) {
        return $false # Mixed - needs fixing
    } else {
        return $false # Pure English - needs translation
    }
}

# Function to translate content using dictionary
function Invoke-BasicTranslation {
    param([string]$Content)
    
    $TranslatedContent = $Content
    
    foreach ($English in $TranslationMap.Keys) {
        $Slovak = $TranslationMap[$English]
        $TranslatedContent = $TranslatedContent -replace "\b$English\b", $Slovak
    }
    
    return $TranslatedContent
}

# Function to standardize YAML structure
function Format-YamlStructure {
    param([string]$Content, [string]$FileName)
    
    # Detect file type from content/filename
    $FileType = "generic"
    if ($FileName -match "char_" -or $Content -match "character") { $FileType = "character" }
    elseif ($FileName -match "faction_" -or $Content -match "faction") { $FileType = "faction" }
    elseif ($Content -match "economy|eddie|market") { $FileType = "economy" }
    elseif ($Content -match "technology|tech|system") { $FileType = "technology" }
    elseif ($Content -match "culture|tradition|lifestyle") { $FileType = "culture" }
    elseif ($Content -match "location|district|landmark") { $FileType = "location" }
    elseif ($Content -match "weapon|combat|damage") { $FileType = "combat" }
    elseif ($Content -match "quest|mission|gig") { $FileType = "quest" }
    
    # Parse existing content to extract key information
    $Lines = $Content -split "`n"
    $Name = ""
    $Id = ""
    $Category = ""
    $Description = ""
    
    foreach ($Line in $Lines) {
        if ($Line -match '^name:\s*"?([^"]+)"?') { $Name = $Matches[1] }
        if ($Line -match '^id:\s*"?([^"]+)"?') { $Id = $Matches[1] }
        if ($Line -match '^category:\s*"?([^"]+)"?') { $Category = $Matches[1] }
        if ($Line -match '^description:\s*"?([^"]+)"?') { $Description = $Matches[1] }
    }
    
    # Build standardized structure
    $StandardizedYaml = @"
type: "$FileType"
title: "$Name"
category: "$Category"
${FileType}_id: "$Id"

content:
  summary: "$Description"
  
$Content

technical_metadata:
  last_updated: "$(Get-Date -Format 'yyyy-MM-dd')"
  translation_status: "automated_bulk_process"
  language: "slovak"

related_cards:
  # TODO: Add related cards during review

notes_for_elena:
  key_points:
    - "Automaticky preložené - skontroluj presnosť"
  conversation_guidelines:
    - "Použi slovenský jazyk s technickými termínmi v EN"
  roleplay_aspects:
    - "Základné informácie pre konverzáciu"
"@

    return $StandardizedYaml
}

# Main processing function
function Process-YamlFile {
    param([string]$FilePath)
    
    try {
        $FileName = Split-Path $FilePath -Leaf
        Write-Log "Processing: $FileName"
        
        # Read current content
        $OriginalContent = Get-Content $FilePath -Raw -Encoding UTF8
        
        # Check if already processed
        if ($OriginalContent -match "translation_status.*automated_bulk_process") {
            Write-Log "Skipping $FileName - already processed" "WARN"
            return $true
        }
        
        # Check if pure Slovak (skip if good)
        if (Test-IsSlovak $OriginalContent) {
            Write-Log "Skipping $FileName - already in Slovak" "INFO"
            return $true
        }
        
        # Backup original
        $BackupFile = Join-Path $BackupDir $FileName
        $BackupSubDir = Split-Path $BackupFile -Parent
        if (!(Test-Path $BackupSubDir)) {
            New-Item -ItemType Directory -Path $BackupSubDir -Force
        }
        Copy-Item $FilePath $BackupFile -Force
        
        # Process content
        $TranslatedContent = Invoke-BasicTranslation $OriginalContent
        $StandardizedContent = Format-YamlStructure $TranslatedContent $FileName
        
        # Write new content (if not dry run)
        if (!$DryRun) {
            Set-Content -Path $FilePath -Value $StandardizedContent -Encoding UTF8
            Write-Log "Processed successfully: $FileName" "INFO"
        } else {
            Write-Log "DRY RUN - Would process: $FileName" "INFO"
        }
        
        return $true
        
    } catch {
        Write-Log "ERROR processing $FileName : $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Main execution
Write-Log "=== ELENA LORE BULK TRANSLATION STARTED ===" "INFO"
Write-Log "Lore Path: $LorePath" "INFO"
Write-Log "Dry Run: $DryRun" "INFO"
Write-Log "Batch Size: $BatchSize" "INFO"
Write-Log "Backup Directory: $BackupDir" "INFO"

# Create backup directory
if (!$DryRun) {
    New-Item -ItemType Directory -Path $BackupDir -Force
    Write-Log "Created backup directory: $BackupDir" "INFO"
}

# Get all YAML files
try {
    $YamlFiles = Get-ChildItem -Path $LorePath -Recurse -Filter "*.yaml" -ErrorAction Stop | Sort-Object FullName
    Write-Log "Found $($YamlFiles.Count) YAML files to process" "INFO"
} catch {
    Write-Log "ERROR: Cannot access lore directory: $($_.Exception.Message)" "ERROR"
    Write-Log "Path attempted: $LorePath" "ERROR"
    exit 1
}

# Process files in batches
$TotalFiles = $YamlFiles.Count
$CurrentBatch = 0

for ($i = 0; $i -lt $TotalFiles; $i += $BatchSize) {
    $CurrentBatch++
    $BatchFiles = $YamlFiles[$i..([Math]::Min($i + $BatchSize - 1, $TotalFiles - 1))]
    
    Write-Log "=== BATCH $CurrentBatch (Files $($i+1)-$([Math]::Min($i + $BatchSize, $TotalFiles))) ===" "INFO"
    
    foreach ($File in $BatchFiles) {
        $Success = Process-YamlFile $File.FullName
        
        if ($Success) {
            $ProcessedCount++
        } else {
            $ErrorCount++
        }
        
        # Progress indicator
        $PercentComplete = [Math]::Round(($ProcessedCount + $ErrorCount) / $TotalFiles * 100, 1)
        Write-Progress -Activity "Processing YAML files" -Status "$PercentComplete% Complete" -PercentComplete $PercentComplete
    }
    
    # Small delay between batches
    Start-Sleep -Milliseconds 100
}

# Final summary
Write-Log "=== BULK TRANSLATION COMPLETED ===" "INFO"
Write-Log "Total files: $TotalFiles" "INFO"
Write-Log "Successfully processed: $ProcessedCount" "INFO"
Write-Log "Errors: $ErrorCount" "INFO"
Write-Log "Success rate: $([Math]::Round(($ProcessedCount / [Math]::Max($TotalFiles, 1)) * 100, 1))%" "INFO"

if ($ErrorCount -gt 0) {
    Write-Log "Check log file for errors: $LogFile" "WARN"
}

Write-Log "Backup location: $BackupDir" "INFO"
Write-Log "Log file: $LogFile" "INFO"
