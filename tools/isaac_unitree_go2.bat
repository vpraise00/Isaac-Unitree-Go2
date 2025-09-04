@echo off
setlocal ENABLEDELAYEDEXPANSION
REM Isaac Sim 5.0 launcher wrapper for go2 runner (Windows 11)

REM Allow overriding the Isaac Sim launcher path via environment variable
IF "%ISAAC_SIM_BAT%"=="" (
  SET "ISAAC_SIM_BAT=D:\My_Project\Sim\isaac-sim-standalone-5.0.0-windows-x86_64\isaac-sim.bat"
)

REM Compute the path to the Python runner script
SET "SCRIPT_DIR=%~dp0"
SET "REPO_ROOT=%SCRIPT_DIR%.."
SET "RUNNER=%SCRIPT_DIR%isaac_unitree_go2.py"

IF NOT EXIST "%ISAAC_SIM_BAT%" (
  echo [ERROR] ISAAC_SIM_BAT not found: %ISAAC_SIM_BAT%
  echo Set ISAAC_SIM_BAT environment variable to your isaac-sim.bat path.
  exit /b 1
)

REM Enable required extensions and execute the Python runner, forwarding all args
"%ISAAC_SIM_BAT%" --enable isaacsim.core.nodes,isaacsim.replicator.writers --exec "%RUNNER%" -- %*

ENDLOCAL@echo off
setlocal
REM Usage: isaac_unitree_go2.bat --run_cfg teleoperation --env warehouse --task go2-locomotion [--render_mode performance|quality|pathtraced]

set ISAAC_BAT="D:\My_Project\Sim\isaac-sim-standalone-5.0.0-windows-x86_64\isaac-sim.bat"

REM If user requested help, print the Python runner's argparse help and exit (without starting Isaac Sim)
set SCRIPT=%~dp0..\tools\isaac_unitree_go2.py
if /I "%1"=="--help" goto :HELP
if /I "%1"=="-h" goto :HELP
if "%1"=="/?" goto :HELP

:RUN

REM Forward all args to the python runner under Isaac Sim
REM Keep args after -- so they're forwarded to Python unchanged
set "ISAAC_RUN_ARGS=%*"
%ISAAC_BAT% --exec "%~dp0..\tools\isaac_unitree_go2.py" -- %*
endlocal
goto :EOF

:HELP
REM Prefer Python launcher 'py', fallback to 'python'
where py >nul 2>&1 && (py -3 "%SCRIPT%" --help) || (python "%SCRIPT%" --help)
exit /b %ERRORLEVEL%
