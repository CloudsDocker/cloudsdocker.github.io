---
header:
    image: /assets/images/hd_geode_ordinal.png
title:  WSL ubuntu used too much spaces to use in my windows
date: 2025-05-29
tags:
 - terraform
 - azure
 - linux
permalink: /blogs/tech/en/clean-up-wsl-space-in-windows
layout: single
category: tech
---

> Take the risk or lose the chance!

# How to Free Up WSL Disk Space Using Compact Command

## Overview
When using Windows Subsystem for Linux (WSL), the virtual disk file can grow over time but doesn't automatically shrink when files are deleted. This guide shows how to reclaim disk space by compacting the WSL virtual disk.

## Prerequisites
- Windows 10/11 with WSL installed
- Administrator privileges on Windows
- WSL distribution (Ubuntu, Debian, etc.)

## Step-by-Step Process

### Step 1: Shutdown WSL
First, ensure all WSL instances are completely shut down:

```powershell
wsl --shutdown
```

**Important:** Wait a few seconds to ensure WSL is fully terminated before proceeding.

### Step 2: Open Command Prompt as Administrator
1. Press `Win + X`
2. Select "Command Prompt (Admin)" or "Windows PowerShell (Admin)"
3. Click "Yes" when prompted by User Account Control

### Step 3: Launch Diskpart
```cmd
diskpart
```

### Step 4: Select the WSL Virtual Disk
In the diskpart prompt, enter the following command:

```diskpart
select vdisk file="C:\Users\%USERNAME%\AppData\Local\Packages\CanonicalGroupLimited.UbuntuonWindows_79rhkp1fndgsc\LocalState\ext4.vhdx"
```

**Note:** The path may vary depending on your WSL distribution and installation method.

### Step 5: Compact the Virtual Disk
```diskpart
compact vdisk
```

This process may take several minutes depending on the size of your virtual disk.

### Step 6: Exit Diskpart
```diskpart
exit
```

## Alternative Virtual Disk Paths

Depending on your WSL distribution, the virtual disk file may be located at different paths:

| Distribution | Typical Path |
|--------------|--------------|
| Ubuntu | `C:\Users\%USERNAME%\AppData\Local\Packages\CanonicalGroupLimited.UbuntuonWindows_79rhkp1fndgsc\LocalState\ext4.vhdx` |
| Ubuntu 20.04 | `C:\Users\%USERNAME%\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu20.04onWindows_79rhkp1fndgsc\LocalState\ext4.vhdx` |
| Ubuntu 22.04 | `C:\Users\%USERNAME%\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu22.04LTS_79rhkp1fndgsc\LocalState\ext4.vhdx` |
| Debian | `C:\Users\%USERNAME%\AppData\Local\Packages\TheDebianProject.DebianGNULinux_76v4gfsz19hv4\LocalState\ext4.vhdx` |

## Finding Your WSL Virtual Disk Location

If you're unsure of the exact path, you can find it using:

```powershell
wsl -l -v
```

Then navigate to:
```
C:\Users\%USERNAME%\AppData\Local\Packages\
```

Look for folders containing your distribution name.

## Complete Command Sequence

Here's the complete sequence to copy and paste:

```cmd
wsl --shutdown
diskpart
select vdisk file="C:\Users\%USERNAME%\AppData\Local\Packages\CanonicalGroupLimited.UbuntuonWindows_79rhkp1fndgsc\LocalState\ext4.vhdx"
compact vdisk
exit
```

## Expected Results

- **Before:** Virtual disk file may be several GB in size
- **After:** Disk file size reduced to actual usage
- **Typical savings:** 20-70% size reduction depending on previous usage

## Troubleshooting

### Error: "The system cannot find the file specified"
- Verify the correct path to your WSL virtual disk
- Ensure WSL is completely shut down
- Check that you're using the correct distribution package name

### Error: "Access is denied"
- Ensure Command Prompt/PowerShell is running as Administrator
- Close any file managers or applications that might be accessing the WSL directory

### Process Takes Long Time
- This is normal for large virtual disks
- Do not interrupt the process
- Typical time: 2-15 minutes depending on disk size

## Best Practices

1. **Regular Maintenance:** Perform this operation monthly or when disk space is low
2. **Before Compacting:** Clean up unnecessary files within WSL first:
   ```bash
   sudo apt autoremove
   sudo apt autoclean
   conda clean --all  # if using conda
   ```
3. **Backup Important Data:** Although safe, consider backing up important WSL data before major maintenance

## Safety Notes

⚠️ **Important Warnings:**
- Always ensure WSL is completely shut down before running diskpart
- Do not interrupt the compact process once started
- This operation is generally safe but backup critical data as a precaution
- The compact operation only reduces disk size; it does not delete your WSL files

## Additional WSL Management Commands

```powershell
# List all WSL distributions
wsl -l -v

# Shutdown specific distribution
wsl -t <distribution-name>

# Restart WSL after compacting
wsl
```

---

**Last Updated:** May 2025  
**Tested On:** Windows 10, Windows 11 with WSL2
