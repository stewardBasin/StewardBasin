@echo off
cd /d C:\Users\Annie\OneDrive\Desktop\StewardBasin

echo =============================== >> archive\data\scheduler_log.txt
echo Started: %date% %time% >> archive\data\scheduler_log.txt

python archive\scripts\update_live_aq.py >> archive\data\scheduler_log.txt 2>&1
echo update_live_aq.py finished: %date% %time% >> archive\data\scheduler_log.txt

python archive\scripts\chpc_station_mapper.py >> archive\data\scheduler_log.txt 2>&1
echo chpc_station_mapper.py finished: %date% %time% >> archive\data\scheduler_log.txt

echo Finished: %date% %time% >> archive\data\scheduler_log.txt