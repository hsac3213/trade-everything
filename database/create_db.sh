#!/bin/bash

sudo mariadb -u root < ./init_db.sql

echo "DB Created!"