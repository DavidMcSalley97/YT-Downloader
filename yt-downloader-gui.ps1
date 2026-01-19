Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase

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

        <Grid Grid.Row="1" Margin="0,0,0,15">
            <Grid.ColumnDefinitions>
                <ColumnDefinition/>
                <ColumnDefinition Width="40"/>
            </Grid.ColumnDefinitions>

            <TextBox x:Name="UrlBox"
                     Height="38"
                     FontSize="14"
                     Background="#1E1E1E"
                     Foreground="White"
                     BorderBrush="#333"
                     Padding="10"
                     VerticalContentAlignment="Center"/>

            <Button x:Name="ClearBtn"
                    Grid.Column="1"
                    Content="X"
                    FontSize="16"
                    Background="#2A2A2A"
                    Foreground="#FF5252"
                    BorderBrush="#333"/>
        </Grid>

        <StackPanel Grid.Row="2" Orientation="Horizontal" Margin="0,0,0,15">
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
                    FontWeight="Bold"/>
        </StackPanel>
    </Grid>
</Window>
"@

$reader = New-Object System.IO.StringReader $XAML
$xmlReader = [System.Xml.XmlReader]::Create($reader)
$Window = [Windows.Markup.XamlReader]::Load($xmlReader)

$UrlBox = $Window.FindName("UrlBox")
$ClearBtn = $Window.FindName("ClearBtn")
$MP3 = $Window.FindName("MP3")
$MP4 = $Window.FindName("MP4")
$LogBox = $Window.FindName("LogBox")
$DownloadBtn = $Window.FindName("DownloadBtn")

function Log($msg) {
    $LogBox.AppendText("$msg`n")
    $LogBox.ScrollToEnd()
}

$ClearBtn.Add_Click({
    $UrlBox.Clear()
})

$DownloadBtn.Add_Click({
    if (-not $UrlBox.Text) {
        Log "❌ Enter a YouTube URL"
        return
    }
    Log "🚀 Download logic goes here"
})

$Window.ShowDialog() | Out-Null
