sudo cp ~/trade-everything/database/certs/pg-server.crt /var/lib/postgresql/16/main/pg-server.crt
sudo cp ~/trade-everything/database/certs/pg-server.key /var/lib/postgresql/16/main/pg-server.key
sudo cp ~/trade-everything/database/certs/MyRootCA.crt /var/lib/postgresql/16/main/MyRootCA.crt

sudo chown postgres:postgres /var/lib/postgresql/16/main/pg-server.crt
sudo chown postgres:postgres /var/lib/postgresql/16/main/pg-server.key
sudo chown postgres:postgres /var/lib/postgresql/16/main/MyRootCA.crt

sudo chmod 644 /var/lib/postgresql/16/main/pg-server.crt
sudo chmod 600 /var/lib/postgresql/16/main/pg-server.key
sudo chmod 644 /var/lib/postgresql/16/main/MyRootCA.crt