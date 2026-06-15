param (
    [string]$action = "help"
)

switch ($action) {
    "up" {
        docker compose --env-file .env -f infra/docker-compose.yml up -d

        while ($true) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8083/connectors" -Method Get -UseBasicParsing -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    break
                }
            } catch {
                Start-Sleep -Seconds 5
            }
        }

        if (Test-Path "infra/minio-sink.json") {
            $jsonConfig = Get-Content -Raw -Path "infra/minio-sink.json"

            try {
                $headers = @{"Content-Type" = "application/json"}
                Invoke-RestMethod -Uri "http://localhost:8083/connectors" -Method Post -Body $jsonConfig -Headers $headers | Out-Null
            } catch {
                if ($_.Exception.Message -match "409") {
                    Write-Host "The connector is already present in the system and does not need to be reprogrammed" -ForegroundColor Gray
                } else {
                    Write-Host "Connector auto-loading error: $_" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "Warning: Configuration file not found: 'infra/minio-sink.json'!" -ForegroundColor Red
        }
    }
    "down" {
        docker compose --env-file .env -f infra/docker-compose.yml down
    }
    "status" {
        docker compose --env-file .env -f infra/docker-compose.yml ps
    }
    "logs" {
        docker compose --env-file .env -f infra/docker-compose.yml logs -f
    }
    default {
        Write-Host "Command: .\run.ps1 [up | down | status | logs]" -ForegroundColor Yellow
    }
}