Write-Host "YT Downloader" -ForegroundColor Cyan
Write-Host ""

$URL = Read-Host "Enter YouTube URL"

$Downloads = Join-Path $env:USERPROFILE "Downloads"
$Output = "$Downloads\%(title)s.%(ext)s"

function Get-CmdPath($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $wg = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages"
    $found = Get-ChildItem $wg -Recurse -Filter "$name.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { return $found.FullName }

    return $null
}

$YTDLP = Get-CmdPath "yt-dlp"
if (-not $YTDLP) {
    Write-Host "Installing yt-dlp..." -ForegroundColor Yellow
    winget install --id yt-dlp.yt-dlp -e --source winget
    $YTDLP = Get-CmdPath "yt-dlp"
}

$FFMPEG = Get-CmdPath "ffmpeg"
if (-not $FFMPEG) {
    Write-Host "Installing ffmpeg..." -ForegroundColor Yellow
    winget install --id Gyan.FFmpeg -e --source winget
    $FFMPEG = Get-CmdPath "ffmpeg"
}

$FFDIR = Split-Path $FFMPEG

Write-Host ""
Write-Host "Choose format:"
Write-Host "1 = MP3 (audio only)"
Write-Host "2 = MP4 (video)"
$choice = Read-Host "Selection"

Write-Host ""
Write-Host "Downloading..." -ForegroundColor Green

if ($choice -eq "1") {
    & $YTDLP `
        --extract-audio `
        --audio-format mp3 `
        --audio-quality 0 `
        --embed-metadata `
        --embed-thumbnail `
        --convert-thumbnails jpg `
        --add-metadata `
        --prefer-free-formats `
        --no-playlist `
        --ffmpeg-location "$FFDIR" `
        --extractor-args "youtube:player_client=android" `
        --progress `
        -o "$Output" `
        "$URL"
}

elseif ($choice -eq "2") {
    & $YTDLP `
        -f "bv*+ba/b" `
        --merge-output-format mp4 `
        --embed-metadata `
        --ffmpeg-location "$FFDIR" `
        --extractor-args "youtube:player_client=android" `
        --progress `
        -o "$Output" `
        "$URL"
}

else {
    Write-Host "Invalid choice." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Completed!" -ForegroundColor Cyan
Write-Host "Saved to: $Downloads"
