#!/bin/bash

echo "==========================================="
echo "  Deploying and Verifying All Servers"
echo "==========================================="
echo ""

# Deploy to LB and AWS
bash deploy.sh

echo ""
echo "==========================================="
echo "  Verifying Code Versions"
echo "==========================================="
echo ""

echo ">>> LB (172.234.172.191)"
ssh root@172.234.172.191 "cd /opt/ytdl && git log -1 --oneline && grep -n 'player_client=web' app/services/youtube_service.py | head -2"

echo ""
echo ">>> AWS (13.60.71.187)" 
ssh admin@13.60.71.187 "cd /opt/ytdl && git log -1 --oneline && grep -n 'player_client=web' app/services/youtube_service.py | head -2"

echo ""
echo ">>> GCP (35.193.12.77)"
ssh 7plus8@35.193.12.77 "cd /opt/ytdl && git log -1 --oneline && grep -n 'player_client=web' app/services/youtube_service.py | head -2"

echo ""
echo "==========================================="
echo "  Deployment Verification Complete"
echo "==========================================="
