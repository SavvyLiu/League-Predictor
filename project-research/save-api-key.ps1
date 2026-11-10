param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Kaggle', 'Riot')]
    [string]$Provider,
    [switch]$Replace
)

$ErrorActionPreference = 'Stop'
if ($Provider -eq 'Kaggle') {
    $keyPath = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.kaggle\access_token'
} else {
    $keyPath = Join-Path $env:LOCALAPPDATA '4al3\credentials\riot-api-key.txt'
}
if ((Test-Path -LiteralPath $keyPath) -and -not $Replace) {
    throw "A credential already exists at $keyPath. Use -Replace to intentionally replace it."
}

$hiddenKey = Read-Host "Paste your $Provider API token/key (input is hidden)" -AsSecureString
$keyPointer = [IntPtr]::Zero
try {
    $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($hiddenKey)
    $keyText = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer).Trim()
    if ([string]::IsNullOrWhiteSpace($keyText)) { throw 'No key supplied; nothing saved.' }
    if ($Provider -eq 'Riot' -and $keyText -notmatch '^RGAPI-[A-Za-z0-9-]+$') {
        throw 'This is not the expected Riot API key format. Copy the API key value beginning RGAPI- from the Developer Portal; no value was saved.'
    }
    if ($Provider -eq 'Kaggle' -and $keyText.StartsWith('{')) {
        throw 'Use a new Kaggle API token from settings/API, not the legacy kaggle.json contents.'
    }
    $keyDirectory = Split-Path -Parent $keyPath
    [IO.Directory]::CreateDirectory($keyDirectory) | Out-Null
    if (-not (Test-Path -LiteralPath $keyPath)) {
        [IO.File]::WriteAllText($keyPath, '')
    }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().User
    $keyAcl = New-Object Security.AccessControl.FileSecurity
    $keyAcl.SetOwner($identity)
    $keyAcl.SetAccessRuleProtection($true, $false)
    $keyAcl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($identity, 'FullControl', 'Allow')))
    $keyAcl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule('NT AUTHORITY\SYSTEM', 'FullControl', 'Allow')))
    Set-Acl -LiteralPath $keyPath -AclObject $keyAcl
    [IO.File]::WriteAllText($keyPath, $keyText, (New-Object Text.UTF8Encoding($false)))
    Write-Output "Saved $Provider credential to $keyPath. Its value was not printed."
} finally {
    if ($keyPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    }
    $keyText = $null
    $hiddenKey.Dispose()
}
