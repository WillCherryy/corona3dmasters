<#
.SYNOPSIS
  Copies the raw H-CO2 data (Bop and Gacesa 2026), the plotting script and the figures into a SEPARATE Windows clone
  of the repository, commits them on the 'test' branch and pushes to GitHub.

.DESCRIPTION
  Safe for the running simulations: it works only in its own clone on the Windows disk (default D:\MASTERS\corona3dmasters_data)
  and never touches the WSL repository (~/corona3dmasters) that the batches use. Later, in Ubuntu, run `git pull origin test`
  (after the batches have finished) to receive the files there.

  Steps: clone (first time) -> check out 'test' and update it -> copy the four raw files and the plotting script ->
  write README.md, MD5SUMS.txt and .gitattributes (raw data stored byte for byte) -> run the plotting script to make the
  figures (unless -SkipFigures) -> show what will be committed -> ask for confirmation -> commit -> push.

.EXAMPLE
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\publish_h_co2.ps1 -DryRun                 # everything except commit and push: check what it would do
  .\publish_h_co2.ps1                         # the real thing (asks before committing)
  .\publish_h_co2.ps1 -SkipFigures            # data and script only
#>
param(
    [string]$DataDir    = "D:\MASTERS\Archive\H-CO2",
    [string]$PlotScript = "D:\MASTERS\plot_h_co2_figures.py",
    [string]$CloneDir   = "D:\MASTERS\corona3dmasters_data",
    [string]$RepoUrl    = "https://github.com/WillCherryy/corona3dmasters.git",
    [string]$Branch     = "test",
    [string]$Message    = "Add raw Bop and Gacesa H-CO2 data, plotting script and figures",
    [switch]$SkipFigures,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Fail([string]$text) { Write-Host "ERROR: $text" -ForegroundColor Red; exit 1 }
function Invoke-Git { & git @args; if ($LASTEXITCODE -ne 0) { Fail "git $($args -join ' ') failed (exit code $LASTEXITCODE)" } }

# ---- checks --------------------------------------------------------------------------------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail "Git for Windows is not installed (https://git-scm.com/download/win)." }
if ($CloneDir -like "*wsl*") { Fail "Do not use a folder inside WSL. Use a folder on the Windows disk, for example D:\MASTERS\corona3dmasters_data." }
if (-not (Test-Path $DataDir)) { Fail "Data folder not found: $DataDir" }
if (-not (Test-Path $PlotScript)) { Fail "Plotting script not found: $PlotScript (put plot_h_co2_figures.py there or use -PlotScript)." }

function Find-One([string]$pattern) {
    $f = Get-ChildItem -Path $DataDir -Recurse -File -Filter $pattern | Select-Object -First 1
    if (-not $f) { Fail "Could not find a file matching '$pattern' under $DataDir" }
    return $f.FullName
}
$cs  = Find-One "*total_and_elastic_CS*"
$d01 = Find-One "*E0.10-DCS*"
$d1  = Find-One "*E1.00-DCS*"
$d5  = Find-One "*E5.00-DCS*"
$res = Find-One "*state-to-state_CS*"
Write-Host "Found raw files:"; $cs, $d01, $d1, $d5, $res | ForEach-Object { Write-Host "  $_" }

# ---- clone / update ------------------------------------------------------------------------------------------
if (-not (Test-Path (Join-Path $CloneDir ".git"))) {
    Write-Host "Cloning $RepoUrl into $CloneDir ..."
    Invoke-Git clone $RepoUrl $CloneDir
}
Set-Location $CloneDir
Invoke-Git fetch origin
Invoke-Git checkout $Branch
Invoke-Git pull --ff-only origin $Branch
$dirty = (& git status --porcelain)
if ($dirty) { Fail "The clone has uncommitted changes. Look at it with 'git status' in $CloneDir first." }

# ---- copy files ----------------------------------------------------------------------------------------------
$rawDir = Join-Path $CloneDir "data\raw\Bop_Gacesa_2026\H-CO2"
New-Item -ItemType Directory -Force -Path $rawDir, (Join-Path $CloneDir "tools") | Out-Null
Copy-Item $cs  (Join-Path $rawDir "H-CO2_total_and_elastic_CS.out") -Force
Copy-Item $d01 (Join-Path $rawDir "E0.10-DCS.txt") -Force
Copy-Item $d1  (Join-Path $rawDir "E1.00-DCS.txt") -Force
Copy-Item $d5  (Join-Path $rawDir "E5.00-DCS.txt") -Force
Copy-Item $res (Join-Path $rawDir "H-CO2_state-to-state_CS.res") -Force
Copy-Item $PlotScript (Join-Path $CloneDir "tools\plot_h_co2_figures.py") -Force

# checksums (md5sum format)
$sums = Get-ChildItem $rawDir -File | Where-Object { $_.Name -notin @("MD5SUMS.txt", "README.md") } | Sort-Object Name | ForEach-Object {
    "{0}  {1}" -f (Get-FileHash $_.FullName -Algorithm MD5).Hash.ToLower(), $_.Name
}
Set-Content -Path (Join-Path $rawDir "MD5SUMS.txt") -Value $sums -Encoding ascii

# store the raw files byte for byte (no line-ending conversion)
$ga = Join-Path $CloneDir ".gitattributes"
$gaLine = "data/raw/** -text"
if (-not (Test-Path $ga) -or -not (Select-String -Path $ga -SimpleMatch $gaLine -Quiet)) { Add-Content -Path $ga -Value $gaLine -Encoding ascii }

$readme = @'
# Raw H + CO2 collision data (Bop and Gacesa 2026), as received

Source: C. T. Bop and M. Gacesa (2026), MNRAS 552, 1-8, doi:10.1093/mnras/stag1696. Data release: Zenodo, doi:10.5281/zenodo.17549249.
Licence of the Zenodo record: CC BY 4.0 (redistribution allowed with attribution); cite the paper and the dataset. The record holds one file, Archive.zip (md5 e1ebc4637a175a5bd142a6512697e551).

The files are unmodified copies of the files received (checksums in MD5SUMS.txt).
Original location: D:\MASTERS\Archive\H-CO2 (cross sections) and D:\MASTERS\Archive\H-CO2\H-CO2_DCS (angle distributions).

| File | Content |
|---|---|
| E0.10-DCS.txt, E1.00-DCS.txt, E5.00-DCS.txt | differential cross sections at collision energies 0.1, 1 and 5 eV (centre-of-mass frame). 27 blocks of 1,800 rows, one per FINAL rotational level j' = 0, 2, ..., 52 of CO2 (initial level j = 0). Header line of each block: `# DFFCSO. ACCUM LEV(I),J(I) = 1 0 LEV(F),J(F) = <level> <j'> , M = 0, WEIGHTED BY 1.00000`. Columns: angle (degrees, 0.1 to 180 in steps of 0.1), differential cross section (Angstrom^2 per steradian). Block 1 (j' = 0) is the elastic channel; the others are rotationally inelastic. |
| H-CO2_state-to-state_CS.res | cross sections into EVERY final level (final j' = 2 x jf), all 149 energies; needed for the levels above j' = 52 that the angle files do not contain (22 MB). Columns: energy (cm^-1), jf, ji, cross section (Angstrom^2). |
| H-CO2_total_and_elastic_CS.out | 149 energies from 8.07 to 40,328 cm^-1 (0.001 to 5 eV). Columns: energy (cm^-1), j, total cross section (Angstrom^2), elastic cross section (Angstrom^2). |

Figures: `tools/plot_h_co2_figures.py` (plain Python 3 with numpy and matplotlib) makes them from these files; results in `docs/figures/h_co2/`.
'@
Set-Content -Path (Join-Path $rawDir "README.md") -Value $readme -Encoding utf8

# ---- figures -------------------------------------------------------------------------------------------------
if (-not $SkipFigures) {
    $py = $null
    if (Get-Command py -ErrorAction SilentlyContinue) { $py = "py" } elseif (Get-Command python -ErrorAction SilentlyContinue) { $py = "python" }
    if (-not $py) { Fail "Python was not found. Install it, or run with -SkipFigures." }
    $figDir = Join-Path $CloneDir "docs\figures\h_co2"
    Write-Host "Making the figures with $py ..."
    & $py $PlotScript --data $DataDir --out $figDir --pdf
    if ($LASTEXITCODE -ne 0) { Fail "The plotting script failed (is numpy and matplotlib installed? py -m pip install numpy matplotlib)." }
}

# ---- show, confirm, commit, push ---------------------------------------------------------------------------
Invoke-Git add data tools .gitattributes
if (-not $SkipFigures) { Invoke-Git add docs }
Write-Host ""; Write-Host "About to commit on branch '$Branch':" -ForegroundColor Cyan
Invoke-Git status --short
if ($DryRun) {
    Write-Host "`nDry run: nothing committed or pushed. To undo what was copied: cd '$CloneDir'; git reset; git clean -fd" -ForegroundColor Yellow
    exit 0
}
$answer = Read-Host "`nCommit with message '$Message' and push to origin/$Branch? (y/N)"
if ($answer -notmatch '^[yY]') { Write-Host "Not committed. The files are staged in $CloneDir (git reset to unstage)."; exit 0 }
Invoke-Git commit -m $Message
Invoke-Git push origin $Branch
Write-Host "`nDone. In Ubuntu, after the batches have finished: cd ~/corona3dmasters; git pull origin $Branch" -ForegroundColor Green
