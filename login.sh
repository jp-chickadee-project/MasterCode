#!/bin/bash

clear
host=$(hostname)
figlet -f slant $host

IP=$(hostname -I)

echo -e "IP:\e[33m $IP"
echo ""
echo -e "\e[39m -------------------------------"
echo "|          Commands:            |"
echo "|                               |"
echo -e "| \e[33mtransmit: \e[39mstarts transmit.out |"
echo -e "| \e[33mbrain: \e[39mstarts brain.py        |"
echo " -------------------------------"


