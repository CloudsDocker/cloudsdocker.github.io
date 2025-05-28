---
header:
    image: /assets/images/hd_geode_ordinal.png
title:  How to Pass the Real Azure VM Name to Your Linux App—Even When $HOSTNAME Fails
date: 2025-05-27
tags:
 - terraform
 - azure
 - linux
permalink: /blogs/tech/en/inject_real_vm_name_in_azure_via_terraform
layout: single
category: tech
---

> Take the risk or lose the chance!

## How to Pass the Real Azure VM Name to Your Linux App—Even When `$HOSTNAME` Fails

When deploying Linux VMs in the cloud, it’s common to need the actual VM name inside your application’s configuration. You might think, “Easy! Just use the `$HOSTNAME` environment variable.” But if you’ve ever tried to reference `$HOSTNAME` in a shell script that’s run by `systemctl` as a service, you’ve probably discovered it doesn’t always work as expected. Why? Because systemd services don’t always inherit the environment you expect, and sometimes `$HOSTNAME` is not set or is set incorrectly.

### The Problem

Let’s say you have a shell script that configures your application, and you want to inject the real VM name into a config file. If you try something like this in your script:

```bash
echo "vm_name=$HOSTNAME" > /etc/myapp/config.ini
```

It might work when you run the script manually, but when systemd runs it as a service, `$HOSTNAME` could be empty or wrong. That’s a headache, especially in automated cloud deployments.

### The Solution: Let Terraform Do the Heavy Lifting

Instead of relying on the Linux environment, you can use your Infrastructure-as-Code tool—Terraform—to inject the real VM name at deployment time. Here’s how we solved it:

#### 1. **Terraform Knows the VM Name**

When you define your Azure Linux VM in Terraform, you control the name:

````terraform
resource "azurerm_linux_virtual_machine" "app" {
  count = var.vm-instance-count
  name  = format("%s-%d", var.app_vm_name, count.index)
  # ...other config...
}
````

#### 2. **Pass the Name to the VM Extension**

Azure’s Custom Script Extension lets you run scripts on your VM after provisioning. You can pass the VM name as a parameter:

````terraform
resource "azurerm_virtual_machine_extension" "custom_script" {
  count              = var.vm-instance-count
  name               = "BuildAndUpgradeScripts"
  virtual_machine_id = azurerm_linux_virtual_machine.app[count.index].id
  publisher          = "Microsoft.Azure.Extensions"
  type               = "CustomScript"
  type_handler_version = "2.1"

  settings = jsonencode({
    "fileUris": [],
    "commandToExecute": <<-EOT
      #!/bin/bash
      /bin/bash /usr/local/bin/build_server.sh "app" "${azurerm_linux_virtual_machine.app[count.index].name}" >> /var/log/custom-script.log 2>&1
    EOT
  })
}
````

Notice how we use `"${azurerm_linux_virtual_machine.app[count.index].name}"`—this is the real, provisioned VM name.

#### 3. **Use the Name in Your Script**

Your shell script can now accept the VM name as a parameter:

```bash
#!/bin/bash
APP_NAME=$1
VM_NAME=$2

echo "vm_name=$VM_NAME" > /etc/myapp/config.ini
```

And when the extension runs, it calls:

```bash
/bin/bash /usr/local/bin/build_server.sh "app" "real-vm-name"
```

No more guessing, no more broken `$HOSTNAME` references.

---

### Why This Works

- **Terraform** knows the VM name at deploy time.
- **Azure Custom Script Extension** lets you pass parameters directly.
- **Your script** gets the real VM name, every time, regardless of how or when it’s run.

### Privacy Note

All company and environment-specific names have been masked for privacy. This pattern works for any cloud, any app, and any organization.

---

**Takeaway:**  
If you need the real VM name inside your Linux app, don’t trust `$HOSTNAME`—let your IaC tool (like Terraform) pass it as a parameter. It’s reliable, repeatable, and cloud-native.

Happy automating!
