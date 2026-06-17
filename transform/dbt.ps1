$envFilePath = "..\.env"

if (Test-Path $envFilePath) {
    Get-Content $envFilePath | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } | ForEach-Object {
        $name, $value = $_.Split('=', 2)
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
    }
} else {
    Write-Host "Warning: .env file not found at $envFilePath" -ForegroundColor Yellow
}

dbt $args