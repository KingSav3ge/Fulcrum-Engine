param(
    [ValidateRange(1, 65535)][int]$Port = 8765,
    [switch]$NoBrowser,
    [ValidateRange(2, 60)][int]$StartupWaitSeconds = 25,
    [string]$AppRoot = ''
)

$ErrorActionPreference = 'Stop'

function Read-IrgsHealthJson([string]$Url) {
    $response = $null
    $reader = $null
    try {
        $request = [System.Net.HttpWebRequest]::Create($Url)
        $request.Method = 'GET'
        $request.Proxy = $null
        $request.Timeout = 1200
        $request.ReadWriteTimeout = 1200
        $response = $request.GetResponse()
        $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
        return ($reader.ReadToEnd() | ConvertFrom-Json)
    } catch {
        return $null
    } finally {
        if ($null -ne $reader) { $reader.Dispose() }
        if ($null -ne $response) { $response.Dispose() }
    }
}

# Both sides must supply the existing host's complete public build snapshot.
# Fingerprints identify selected files; they do not replace release verification.
function Test-IrgsBuildIdentity($Actual, $Expected) {
    if ($null -eq $Actual -or $null -eq $Expected) { return $false }
    $hashFields = @('app_manifest_sha256', 'host_source_sha256',
        'engine_manifest_sha256', 'engine_core_sha256',
        'catalog_manifest_sha256', 'catalog_portfolio_sha256')
    foreach ($identity in @($Actual, $Expected)) {
        if (-not (($identity.schema_version -is [int]) -or ($identity.schema_version -is [long])) -or
            $identity.schema_version -ne 1) { return $false }
        if ($identity.edition -isnot [string] -or $identity.edition -cnotmatch '^\d+\.\d+\.\d+$' -or
            $identity.classification -isnot [string]) { return $false }
        $classification = if ($identity.edition.StartsWith('3.')) { 'pre_alpha' } else { 'unclassified' }
        if ($identity.classification -cne $classification) { return $false }
        foreach ($field in $hashFields) {
            $hash = $identity.$field
            if ($hash -isnot [string] -or $hash -cnotmatch '^[0-9a-f]{64}$') { return $false }
        }
    }
    foreach ($field in (@('edition', 'classification') + $hashFields)) {
        if ($Actual.$field -cne $Expected.$field) { return $false }
    }
    return $true
}

function Get-IrgsExpectedBuild([string]$PythonPath, [string]$HostFolder, [string]$SuiteFolder) {
    try {
        # Use the very same selected App/Engine/Catalog resolver as the host.
        # Pass the folder as an argument; never interpolate a path into code.
        $code = 'import json,sys;sys.path.insert(0,sys.argv[1]);from build_identity import running_build;print(json.dumps(running_build()))'
        $output = @(& $PythonPath -B -c $code $HostFolder 2>&1)
        if ($LASTEXITCODE -ne 0) { throw 'identity process failed' }
        $identity = ($output -join [Environment]::NewLine) | ConvertFrom-Json
        if (-not (Test-IrgsBuildIdentity $identity $identity)) { throw 'incomplete identity' }
        # Do not let an unrelated Engine override silently replace the suite
        # selected by this launcher. Compare the same files used in the snapshot.
        $manifestHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $SuiteFolder 'release.json')).Hash.ToLowerInvariant()
        $coreHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path (Join-Path $SuiteFolder 'runtime') 'core_world.py')).Hash.ToLowerInvariant()
        if ($identity.engine_manifest_sha256 -cne $manifestHash -or $identity.engine_core_sha256 -cne $coreHash) {
            throw 'selected Engine differs'
        }
        return $identity
    } catch {
        throw 'IRGS cannot establish the selected App, Engine and Catalog build. Check the installed components and IRGS_ENGINE_ROOT/IRGS_CATALOG_ROOT, then try again. No application was stopped.'
    }
}

function Get-IrgsHostState([int]$HostPort, $ExpectedBuild) {
    $baseUrl = "http://127.0.0.1:$HostPort"
    $catalogue = Read-IrgsHealthJson "$baseUrl/api/catalog"
    if ($null -ne $catalogue -and $catalogue.core.id -eq 'IRGS-CORE-3.3' -and
        [string]$catalogue.core.version -eq '3.3' -and $catalogue.core.single_world_per_campaign -eq $true) {
        $session = Read-IrgsHealthJson "$baseUrl/api/campaigns"
        if ($null -ne $session -and $session.PSObject.Properties.Name -contains 'campaigns' -and
            $session.campaigns -is [array] -and $session.token -is [string] -and $session.token.Length -ge 16 -and
            (Test-IrgsBuildIdentity $session.build $ExpectedBuild)) {
            return 'Ready'
        }
    }
    $connection = New-Object System.Net.Sockets.TcpClient
    $pending = $null
    try {
        $pending = $connection.BeginConnect('127.0.0.1', $HostPort, $null, $null)
        if (-not $pending.AsyncWaitHandle.WaitOne(300)) {
            # A timeout is uncertain, not proof that the port is free.
            return 'Occupied'
        }
        $connection.EndConnect($pending)
        return 'Occupied'
    } catch {
        $cause = $_.Exception
        while ($null -ne $cause.InnerException) { $cause = $cause.InnerException }
        if ($cause -is [System.Net.Sockets.SocketException] -and
            $cause.SocketErrorCode -eq [System.Net.Sockets.SocketError]::ConnectionRefused) {
            return 'Stopped'
        }
        # Any other probe failure is uncertain; do not try to claim the port.
        return 'Occupied'
    } finally {
        if ($null -ne $pending) { $pending.AsyncWaitHandle.Close() }
        $connection.Close()
    }
}

function Confirm-IrgsRelease([string]$PythonPath, [string]$SuiteFolder) {
    $verification = & $PythonPath -B (Join-Path $SuiteFolder 'runtime\irgs.py') verify 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "IRGS could not verify its installed files. No new host was started. Restore the complete release package and try again.`n$($verification -join [Environment]::NewLine)"
    }
}

function Start-IrgsWebsite([int]$HostPort, [bool]$OpenBrowser, [int]$WaitSeconds) {
    $suiteFolder = $PSScriptRoot
    $hostFolder = Join-Path (Split-Path $suiteFolder -Parent) 'IRGS_Web'
    if ($AppRoot) { $hostFolder = $AppRoot }
    $hostEntry = Join-Path $hostFolder 'server.py'
    if (-not (Test-Path -LiteralPath $hostEntry -PathType Leaf)) {
        throw 'IRGS cannot locate the selected App host. Check the installed components. No application was stopped.'
    }
    $hostFolder = (Resolve-Path -LiteralPath $hostFolder).ProviderPath
    $hostEntry = Join-Path $hostFolder 'server.py'
    $suitePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (-not (Test-Path -LiteralPath $suitePython)) {
        $suitePython = (Get-Command python -CommandType Application -ErrorAction Stop).Source
    }
    $mutex = New-Object System.Threading.Mutex($false, "Local\IRGS-Core-3.3-Port-$HostPort")
    $held = $false
    try {
        try { $held = $mutex.WaitOne(45000) }
        catch [System.Threading.AbandonedMutexException] { $held = $true }
        if (-not $held) { throw 'IRGS is already starting in another window. Please try again shortly.' }
        $expectedBuild = Get-IrgsExpectedBuild $suitePython $hostFolder $suiteFolder
        $state = Get-IrgsHostState $HostPort $expectedBuild
        if ($state -eq 'Occupied') {
            throw "Port $HostPort is occupied by an application or a different or unidentified IRGS build. It has been left running. Choose another port using -Port and try again."
        }
        Confirm-IrgsRelease $suitePython $suiteFolder
        # Verification may take time; resnapshot the selected files and recheck.
        $expectedBuild = Get-IrgsExpectedBuild $suitePython $hostFolder $suiteFolder
        $state = Get-IrgsHostState $HostPort $expectedBuild
        if ($state -eq 'Occupied') {
            throw "Port $HostPort is occupied by an application or a different or unidentified IRGS build. It has been left running. Choose another port using -Port and try again."
        }
        if ($state -ne 'Ready') {
            $liveFolder = Join-Path $suiteFolder 'live'
            [System.IO.Directory]::CreateDirectory($liveFolder) | Out-Null
            $stamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fff') + "-$PID"
            $stdout = Join-Path $liveFolder "host-$stamp-stdout.log"
            $stderr = Join-Path $liveFolder "host-$stamp-stderr.log"
            $arguments = @('-B', ('"' + $hostEntry + '"'), '--port', [string]$HostPort)
            $hostProcess = Start-Process -FilePath $suitePython -ArgumentList $arguments -WorkingDirectory $hostFolder `
                -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
            $deadline = [DateTime]::UtcNow.AddSeconds($WaitSeconds)
            $state = 'Stopped'
            do {
                $state = Get-IrgsHostState $HostPort $expectedBuild
                if ($state -eq 'Ready') { break }
                $hostProcess.Refresh()
                if ($hostProcess.HasExited) { break }
                Start-Sleep -Milliseconds 250
            } while ([DateTime]::UtcNow -lt $deadline)
            if ($state -ne 'Ready') {
                throw "IRGS did not become ready with the selected build. No running application was stopped. Check $stderr or choose a different port using -Port."
            }
            $expectedBuild = Get-IrgsExpectedBuild $suitePython $hostFolder $suiteFolder
            if ((Get-IrgsHostState $HostPort $expectedBuild) -ne 'Ready') {
                throw "The running host no longer matches the selected build on port $HostPort. It has been left running. Choose another port using -Port."
            }
            $metadataPath = Join-Path $liveFolder 'host_process.json'
            $metadataTemp = $metadataPath + '.tmp'
            $metadata = @{entry = $hostEntry; process_id = $hostProcess.Id; port = $HostPort} | ConvertTo-Json
            [System.IO.File]::WriteAllText($metadataTemp, $metadata, (New-Object System.Text.UTF8Encoding($false)))
            Move-Item -LiteralPath $metadataTemp -Destination $metadataPath -Force
            Write-Host 'IRGS is ready. It will keep running after this window closes.'
        } else {
            $expectedBuild = Get-IrgsExpectedBuild $suitePython $hostFolder $suiteFolder
            if ((Get-IrgsHostState $HostPort $expectedBuild) -ne 'Ready') {
                throw "The running host no longer matches the selected build on port $HostPort. It has been left running. Choose another port using -Port."
            }
            Write-Host 'IRGS is already running. Reusing the existing website.'
        }
        $url = "http://127.0.0.1:$HostPort"
        if ($OpenBrowser) { Start-Process -FilePath $url }
        Write-Host $url
    } finally {
        if ($held) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
}

# Dot-sourcing exposes the read-only probe for launcher fixture tests.
if ($MyInvocation.InvocationName -ne '.') {
    try {
        Start-IrgsWebsite -HostPort $Port -OpenBrowser (-not $NoBrowser) -WaitSeconds $StartupWaitSeconds
        exit 0
    } catch {
        Write-Host ''
        Write-Host ('IRGS could not open: ' + $_.Exception.Message) -ForegroundColor Red
        exit 1
    }
}
