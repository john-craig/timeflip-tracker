```
docker build -t timeflip-server .
sudo docker run --privileged -v /var/run/dbus/:/var/run/dbus/ timeflip-server
```

```
docker run --name mariadb -p 3307:3306 -e MARIADB_RANDOM_ROOT_PASSWORD=1 -e MARIADB_DATABASE=timeflip -e MARIADB_USER=timeflip -e MARIADB_PASSWORD=password mariadb:latest
```

```
MARIADB_HOST=0.0.0.0 MARIADB_PORT=3307 MARIADB_DATABASE=timeflip MARIADB_USER=timeflip MARIADB_PASSWORD=password CONFIG_PATH=./config.yaml python timeflip-tracker/main.py
```
