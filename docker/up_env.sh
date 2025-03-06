#!/bin/bash
cp .env .env.bak
grep -v '^HOSTIP=' .env.bak > .env
HOSTIP=$(hostname -I | awk '{print $1}')
echo -n "HOSTIP=$HOSTIP" >> .env
rm .env.bak