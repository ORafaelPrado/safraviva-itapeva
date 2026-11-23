# Agenda a rotina diária do SafraViva no Agendador de Tarefas do Windows (todo dia às 6h).
#   powershell -ExecutionPolicy Bypass -File scripts\agendar_rotina.ps1            # cria/atualiza
#   powershell -ExecutionPolicy Bypass -File scripts\agendar_rotina.ps1 -Remover   # remove
# Roda só com o usuário logado (não pede senha). Se o computador estiver desligado às 6h,
# a tarefa roda assim que ele for ligado (StartWhenAvailable).
param([switch]$Remover)

$nome = "SafraViva - rotina diaria"
if ($Remover) {
    Unregister-ScheduledTask -TaskName $nome -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output "Tarefa '$nome' removida."
    return
}

$raiz = Split-Path -Parent $PSScriptRoot
$python = Join-Path $raiz ".venv\Scripts\python.exe"
$acao = New-ScheduledTaskAction -Execute $python -Argument "-m scripts.rotina_diaria" -WorkingDirectory $raiz
$gatilho = New-ScheduledTaskTrigger -Daily -At 6:00am
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $nome -Action $acao -Trigger $gatilho -Settings $config `
    -Description "Atualiza previsao, clima, estimativas de safra e alertas do SafraViva (Itapeva-SP)." -Force | Out-Null
Write-Output "Tarefa '$nome' agendada: todo dia as 6h. Log em data\logs\."
