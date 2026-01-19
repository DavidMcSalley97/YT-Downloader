Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase

# GUI
$XAML = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="YT Downloader"
        Height="420"
        Width="620"
        WindowStartupLocation="CenterScreen"
        Background="#121212"
        ResizeMode="NoResize">

    <Grid Margin="20">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <TextBlock Text="YT Downloader"
                   FontSize="26"
                   FontWeight="SemiBold"
                   Foreground="#00E5FF"
                   Margin="0,0,0,20"/>

        <TextBox x:Name="UrlBox"
                 Grid.Row="1"
                 Height="38"
                 FontSize="14"
                 Background="#1E1E1E"
                 Foreground="White"
                 BorderBrush="#333"
                 Padding="10"/>

        <StackPanel Grid.Row="2" Orientation="Horizontal" Margin="0,15,0,15">
            <RadioButton x:Name="MP3" Content="MP3 (Audio)" IsChecked="True" Foreground="White" Margin="0,0,20,0"/>
            <RadioButton x:Name="MP4" Content="MP4 (Video)" Foreground="White"/>
        </StackPanel>

        <TextBox x:Name="LogBox"
                 Grid.Row="3"
                 Background="#0D0D0D"
                 Foreground="#00FF9C"
                 FontFamily="Consolas"
                 FontSize="12"
                 IsReadOnly="True"
                 VerticalScrollBarVisibility="Auto"/>

<StackPanel Grid.Row="4" Orientation="Horizontal" HorizontalAlignment="Right" Margin="0,15,0,0">
    <Button x:Name="DownloadBtn"
            Content="Download"
            Width="120"
            Height="36"
            Background="#00E5FF"
            Foreground="Black"
            FontWeight="Bold"
            Margin="0,0,10,0"/>
    
    <Button x:Name="ClearAllBtn"
            Content="Clear All"
            Width="120"
            Height="36"
            Background="#FF5252"
            Foreground="White"
            FontWeight="Bold"/>
</StackPanel>

    </Grid>
</Window>
"@

$reader = New-Object System.IO.StringReader $XAML
$xmlReader = [System.Xml.XmlReader]::Create($reader)
$Window = [Windows.Markup.XamlReader]::Load($xmlReader)

$UrlBox = $Window.FindName("UrlBox")
$MP3 = $Window.FindName("MP3")
$MP4 = $Window.FindName("MP4")
$LogBox = $Window.FindName("LogBox")
$DownloadBtn = $Window.FindName("DownloadBtn")
$ClearAllBtn = $Window.FindName("ClearAllBtn")
$ClearAllBtn.Add_Click({
    $UrlBox.Clear()
    $LogBox.Clear()
    $MP3.IsChecked = $true
    $MP4.IsChecked = $false
    Log "Cleared as james requested, ready for new download."
})
# logging
function Log {
    param($msg)
    $Window.Dispatcher.Invoke([action]{
        $LogBox.AppendText("$msg`n")
        $LogBox.ScrollToEnd()
    })
}

# find binary
function Find-Binary($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" |
        Get-ChildItem -Recurse -Filter "$name.exe" -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
}

# download handler
$DownloadBtn.Add_Click({

    $url = $UrlBox.Text.Trim()
    if (-not $url) { Log "No URL provided"; return }

    $DownloadBtn.IsEnabled = $false

    $yt = Find-Binary "yt-dlp"
    $ff = Find-Binary "ffmpeg"

    if (-not $yt) { Log "yt-dlp NOT found. Install it first."; $DownloadBtn.IsEnabled = $true; return }
    if (-not $ff) { Log "ffmpeg NOT found. Install it first."; $DownloadBtn.IsEnabled = $true; return }

    $downloads = Join-Path $env:USERPROFILE "Downloads"

    $args = @(
        "--no-playlist"
        "--paths", "home:$downloads"
        "--restrict-filenames"
        "--embed-metadata"
        "--extractor-args", "youtube:player_client=android,web"
    )

    if ($MP3.IsChecked) {
        $args += @("--extract-audio","--audio-format","mp3","--audio-quality","0")
    } else {
        $args += @("-f","bv*+ba/b","--merge-output-format","mp4")
    }

    $args += $url

    Log "Downloading..."
    Log "Output folder: $downloads"

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $yt
    $psi.Arguments = ($args -join " ")
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    $p.Start() | Out-Null

    while (-not $p.HasExited) {
        if (-not $p.StandardOutput.EndOfStream) {
            Log ($p.StandardOutput.ReadLine())
        }
        Start-Sleep -Milliseconds 50
    }

    while (-not $p.StandardError.EndOfStream) {
        Log ($p.StandardError.ReadLine())
    }

    Log "Done."
    $DownloadBtn.IsEnabled = $true
})

$Window.ShowDialog() | Out-Null


