# To find out the port numbers running in servers


## Windows
- To start powershell (with administrator permission)
- Run below below script
  ```shell
  netstat -an | Select-String "LISTENING" | ForEach-Object { [regex]::Matches($_, '\d+').Value } | Sort-Object -Unique
  ```
  
