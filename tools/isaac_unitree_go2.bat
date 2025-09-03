@echo off
setlocal
REM Usage: isaac_unitree_go2.bat --run_cfg teleoperation --env warehouse --task go2-locomotion

set ISAAC_BAT="D:\My_Project\Sim\isaac-sim-standalone-5.0.0-windows-x86_64\isaac-sim.bat"

REM Forward all args to the python runner under Isaac Sim
%ISAAC_BAT% --enable isaacsim.core.nodes,isaacsim.replicator.writers --exec "%~dp0..\tools\isaac_unitree_go2.py" -- %*
endlocal
