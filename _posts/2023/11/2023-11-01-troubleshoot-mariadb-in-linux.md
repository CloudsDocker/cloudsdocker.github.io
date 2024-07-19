# The simplest way to check an mariadb is runnning
```shell
systemctl status mariadb
```

● mariadb.service - MariaDB 10.3 database server
   Loaded: loaded (/usr/lib/systemd/system/mariadb.service; enabled; vendor preset: disabled)
   Active: active (running) since Wed 2023-11-01 08:02:11 AEDT; 6h ago
     Docs: man:mysqld(8)
           https://mariadb.com/kb/en/library/systemd/
  Process: 1869 ExecStartPost=/usr/libexec/mysql-check-upgrade (code=exited, status=0/SUCCESS)
  Process: 1278 ExecStartPre=/usr/libexec/mysql-prepare-db-dir mariadb.service (code=exited, status=0/SUCCESS)
  Process: 1225 ExecStartPre=/usr/libexec/mysql-check-socket (code=exited, status=0/SUCCESS)
 Main PID: 1320 (mysqld)
   Status: "Taking your SQL requests now..."
    Tasks: 49 (limit: 50675)
   Memory: 1.0G
   CGroup: /system.slice/mariadb.service
           └─1320 /usr/libexec/mysqld --basedir=/usr
