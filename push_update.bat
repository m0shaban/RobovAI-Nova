@echo off
git add .
git commit -m "Update logo, favicon, and enhance UI/UX"
git push > push_log.txt 2>&1
echo Done >> push_log.txt
