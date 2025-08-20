---
header:
    image: /assets/images/hd_spring_boot_run_magic.png
title:  Azure Linux VMs Troubleshooting Application-Consistent Backup Azure Linux VMs
date: 2025-08-20
tags:
    - tech
permalink: /blogs/tech/en/azure-linux-vms-troubleshooting-application-consistent-backup-azure-linux-vms
layout: single
category: tech
---
> We know what we are, but know not what we may be. - William Shakespeare

# Troubleshooting and Enabling Application-Consistent Backup for Azure Linux VMs: A Complete Guide

*By Todd - Senior Cloud Infrastructure Engineer*

## Introduction

Application-consistent backups are crucial for ensuring data integrity when restoring Azure Linux VMs. However, many administrators struggle with properly configuring the pre-script and post-script framework required for this functionality. After extensive troubleshooting and testing, I've successfully enabled application-consistent backups and want to share the complete process, common pitfalls, and an automated solution.

## Understanding Application-Consistent Backups

Azure Backup provides different levels of consistency for VM snapshots <mcreference link="https://learn.microsoft.com/en-us/azure/backup/backup-azure-vms-introduction#snapshot-creation" index="3">3</mcreference>:

- **Crash-consistent**: Basic snapshot without application coordination
- **File-system consistent**: Ensures file system integrity
- **Application-consistent**: Coordinates with applications to ensure data consistency

For Linux VMs, achieving application consistency requires custom pre-script and post-script configuration <mcreference link="https://learn.microsoft.com/en-us/azure/backup/backup-azure-linux-app-consistent#configure-prescript-and-post-script-for-azure-linux-vm" index="0">0</mcreference>.

## The Challenge: Common Configuration Issues

During my implementation, I encountered several critical issues that prevented application-consistent backups from working:

### 1. Incorrect File Permissions
The most common issue is improper file permissions. Azure's documentation is very specific about this <mcreference link="https://learn.microsoft.com/en-us/azure/backup/backup-azure-linux-app-consistent#configure-prescript-and-post-script-for-azure-linux-vm" index="0">0</mcreference>:

- **VMSnapshotScriptPluginConfig.json**: Permission **600** (read/write for root only)
- **Pre-script file**: Permission **700** (read/write/execute for root only)
- **Post-script file**: Permission **700** (read/write/execute for root only)

### 2. Non-functional Scripts
Many administrators copy template scripts without ensuring they perform actual work for their specific systems. The scripts must:
- Actually interact with your applications (e.g., stop/start Apache, Tomcat, databases)
- Be thoroughly tested manually before deployment
- Handle errors gracefully

### 3. Ownership Issues
All files must be owned by the **root** user. This is a security requirement that cannot be bypassed.

## The Solution: Step-by-Step Implementation

> First of all, if you want to have an automated solution, please check out my script from below link :  https://github.com/CloudsDocker/cloud-auto-kits/blob/main/devops/setup_application_consistent_backup_opensource.py



### Step 1: Create the Directory Structure
```bash
sudo mkdir -p /etc/azure
cd /etc/azure
```

### Step 2: Download and Configure the Plugin Config
Download the configuration file from Microsoft's official repository <mcreference link="https://github.com/MicrosoftAzureBackup/VMSnapshotPluginConfig" index="1">1</mcreference>:

```bash
sudo wget https://raw.githubusercontent.com/MicrosoftAzureBackup/VMSnapshotPluginConfig/master/VMSnapshotScriptPluginConfig.json
```

Edit the configuration to point to your scripts:
```json
{
  "pluginName": "ScriptRunner",
  "preScriptLocation": "/etc/azure/pre_backup.sh",
  "postScriptLocation": "/etc/azure/post_backup.sh",
  "preScriptParams": ["", ""],
  "postScriptParams": ["", ""],
  "preScriptNoOfRetries": 0,
  "postScriptNoOfRetries": 0,
  "timeoutInSeconds": 30,
  "continueBackupOnFailure": true,
  "fsFreezeEnabled": true
}
```

### Step 3: Create Functional Pre and Post Scripts

**Pre-backup script** (`pre_backup.sh`):
```bash
#!/bin/bash

# Define logging function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | sudo tee -a /var/log/azure-backup.log > /dev/null
}

# Pause the application before backup
log_message "Pre-backup script started - pausing application"

# Check if the service is running before attempting to stop it
if systemctl is-active --quiet myapp.service; then
    sudo systemctl stop myapp.service
    if [ $? -eq 0 ]; then
        log_message "Successfully stopped myapp.service"
    else
        log_message "WARNING: Failed to stop myapp.service"
        # Continue anyway, as we don't want to fail the backup
    fi
else
    log_message "myapp.service was not running, nothing to stop"
fi

# Flush any filesystem buffers
sync

log_message "Pre-backup script completed"
exit 0
```

**Post-backup script** (`post_backup.sh`):
```bash
#!/bin/bash

# Define logging function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | sudo tee -a /var/log/azure-backup.log > /dev/null
}

# Resume the application after backup
log_message "Post-backup script started - resuming application"

# Start the service
sudo systemctl start myapp.service
if [ $? -eq 0 ]; then
    log_message "Successfully started myapp.service"
else
    log_message "ERROR: Failed to start myapp.service"
    # We don't exit with error as we don't want to mark the backup as failed
    # but this should be investigated
fi

log_message "Post-backup script completed"
exit 0
```

### Step 4: Set Correct Permissions
```bash
# Set permission to 600 for VMSnapshotScriptPluginConfig.json
sudo chmod 600 /etc/azure/VMSnapshotScriptPluginConfig.json

# Set permission to 700 for pre_backup.sh
sudo chmod 700 /etc/azure/pre_backup.sh

# Set permission to 700 for post_backup.sh
sudo chmod 700 /etc/azure/post_backup.sh

# Ensure root ownership
sudo chown root:root /etc/azure/VMSnapshotScriptPluginConfig.json
sudo chown root:root /etc/azure/pre_backup.sh
sudo chown root:root /etc/azure/post_backup.sh
```

### Step 5: Test Your Scripts
**Critical**: Always test your scripts manually before relying on them:
```bash
sudo /etc/azure/pre_backup.sh
sudo /etc/azure/post_backup.sh
```

## Troubleshooting Tips

### Check Extension Logs
Monitor the Azure backup extension logs for errors:
```bash
sudo tail -f /var/log/azure/Microsoft.Azure.RecoveryServices.VMSnapshotLinux/extension.log
```

### Verify Script Execution
Ensure your scripts are actually being called and executing successfully by adding verbose logging.

### Common Error Messages
- **Permission denied**: Check file permissions and ownership
- **Script not found**: Verify paths in VMSnapshotScriptPluginConfig.json
- **Timeout errors**: Increase timeoutInSeconds in configuration

## Security Considerations

The framework provides significant power and must be secured properly <mcreference link="https://learn.microsoft.com/en-us/azure/backup/backup-azure-linux-app-consistent#configure-prescript-and-post-script-for-azure-linux-vm" index="0">0</mcreference>:

- Only root user should have access to critical JSON and script files
- If requirements aren't met, scripts won't run, resulting in file system crash and inconsistent backup
- Regular security audits of script content and permissions

## Automated Solution: One-Click Setup

To simplify this process, I've created an automated Python script that handles the entire configuration with a single command. The script:

- Creates the `/etc/azure` directory
- Generates all required files with embedded content
- Sets correct permissions automatically
- Validates the configuration

**Usage:**
```bash
sudo python3 setup_application_consistent_backup.py
```

This script eliminates manual errors and ensures consistent deployment across multiple VMs.

## Conclusion

Enabling application-consistent backups for Azure Linux VMs requires careful attention to:
1. Proper file permissions (600 for config, 700 for scripts)
2. Root ownership of all files
3. Functional scripts that actually interact with your applications
4. Thorough testing before production deployment

By following this guide and using the automated setup script, you can reliably implement application-consistent backups and avoid the common pitfalls that cause backup failures.

## References

- [Configure application-consistent backup for Azure Linux VMs](https://learn.microsoft.com/en-us/azure/backup/backup-azure-linux-app-consistent#configure-prescript-and-post-script-for-azure-linux-vm)
- [VMSnapshotPluginConfig Repository](https://github.com/MicrosoftAzureBackup/VMSnapshotPluginConfig)
- [Azure VM Backup Introduction](https://learn.microsoft.com/en-us/azure/backup/backup-azure-vms-introduction#snapshot-creation)

---

*Have questions or encountered different issues? Feel free to reach out in the comments below. Happy backing up!*
