---
header:
    image: /assets/images/hd_cpu_system_info_aws.jpg
title:  Mastering-Terraform Injecting-Shell-Scripts-into-Linux-VMs-Like-a-Pro
date: 2025-03-22
tags:
    - tech
    - terraform
    - DevOps
permalink: /blogs/tech/en/Mastering-Terraform-Injecting-Shell-Scripts-into-Linux-VMs-Like-a-Pro
layout: single
category: tech
---
> The only impossible journey is the one you never begin. - Tony Robbins

# Mastering Terraform: Injecting Shell Scripts into Linux VMs Like a Pro

Ever felt like you're playing a game of "telephone" with your cloud infrastructure? You write a script, pass it to the VM, and hope it executes correctly. Well, today we're going to turn that game into a well-orchestrated symphony using Terraform. Let's dive into the art of injecting shell scripts into Linux VMs with style and precision!

## The Problem: Scripts Gone Rogue

Picture this: You've got a brilliant shell script that sets up your Linux VM perfectly. But every time you update it, you're manually copying it to the VM, crossing your fingers, and hoping it works. Sounds familiar? We've all been there. But what if I told you there's a better way?

## The Solution: Terraform's Magic Wand

We're going to use Terraform to:
1. Read our shell script from the project folder
2. Inject it into our Linux VM during creation
3. Execute it automatically
4. Verify the results like a pro

## Step 1: The Setup

First, let's organize our project. Here's what your folder structure might look like:

```
/terraform-project
├── main.tf
├── variables.tf
├── outputs.tf
└── scripts/
    └── setup_server.sh
```

Our `setup_server.sh` is a simple script that installs some packages and configures the server:

```bash
#!/bin/bash
echo "Starting server setup..."
sudo apt-get update
sudo apt-get install -y nginx
echo "Server setup complete! 🎉"
```

## Step 2: The Terraform Magic

Here's how we'll make the magic happen in our `main.tf`:

```hcl
# Read the script file
locals {
  setup_script = file("${path.module}/scripts/setup_server.sh")
}

# Create the Linux VM
resource "azurerm_linux_virtual_machine" "web_server" {
  # ... (your VM configuration) ...
}

# Inject and execute the script
resource "azurerm_virtual_machine_extension" "setup_script" {
  name                 = "setup-script"
  virtual_machine_id   = azurerm_linux_virtual_machine.web_server.id
  publisher            = "Microsoft.Azure.Extensions"
  type                 = "CustomScript"
  type_handler_version = "2.1"

  settings = jsonencode({
    "commandToExecute" = <<-EOT
      #!/bin/bash
      echo '${local.setup_script}' > /tmp/setup_server.sh
      chmod +x /tmp/setup_server.sh
      /tmp/setup_server.sh > /var/log/setup.log 2>&1
    EOT
  })
}
```

## Step 3: Deployment Dance

Now, let's deploy our masterpiece:

```bash
terraform init
terraform apply
```

Watch as Terraform orchestrates the creation of your VM and the execution of your script. It's like watching a well-rehearsed ballet!

## Step 4: Verification Station

After the VM is up and running, let's check if our script worked:

```bash
# SSH into your VM
ssh azureuser@your-vm-ip

# Check the setup log
cat /var/log/setup.log

# Verify Nginx is installed
systemctl status nginx
```

If you see "Server setup complete! 🎉" in the log and Nginx running, congratulations! You've just automated server setup like a pro.

## Pro Tips for the Road

1. **Version Control Your Scripts**: Treat your scripts like code (because they are!). Use Git to track changes.
2. **Parameterize Your Scripts**: Use Terraform variables to make your scripts more flexible.
3. **Error Handling**: Add error checking in your scripts and monitor the logs.
4. **Security**: Never hard-code sensitive information. Use Terraform's sensitive variables or Azure Key Vault.

## The Grand Finale

Remember that game of "telephone" we talked about? With this approach, you've turned it into a well-oiled machine. Your scripts are version-controlled, automatically deployed, and verified. You're not just managing infrastructure; you're orchestrating it.

So go forth, automate with confidence, and remember: in the world of cloud infrastructure, the only thing that should be manual is the high-five you give yourself after a successful deployment! 🖐️

Happy Terraforming! 🚀