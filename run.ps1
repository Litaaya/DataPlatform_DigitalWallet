param (
    [string]$action = "help"
)

switch ($action) {
    "up" {
        docker compose --env-file .env -f infra/docker-compose.yml up -d
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