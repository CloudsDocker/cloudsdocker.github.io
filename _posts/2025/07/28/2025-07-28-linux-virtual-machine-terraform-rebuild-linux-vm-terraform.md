
---
header:
    image: /assets/images/hd_mvn_skip_tests.png
title:  linux virtual machine terraform rebuild Linux VM Terraform
date: 2025-07-28
tags:
    - tech
permalink: /blogs/tech/en/linux-virtual-machine-terraform-rebuild-linux-vm-terraform
layout: single
category: tech
---
> In three words I can sum up everything I've learned about life: it goes on. - Robert Frost

# Why Your Azure VM Just Got Rebuilt: A Terraform Detective Story 🕵️

*When infrastructure code meets immutable resources, sometimes things need to start fresh.*

---

## The Mystery Unfolds

You run `terraform plan`, expecting a routine update. Instead, you're greeted with a wall of red text showing your VM will be **destroyed and recreated**. Your heart skips a beat. *What went wrong?*

Don't panic. This is actually Terraform working exactly as designed. Let me walk you through what happened and why.

## The Smoking Gun 🔍

```hcl
source_image_id:
"/subscriptions/.../versions/2025.06.17010625"
change to
"/subscriptions/.../versions/2025.07.22055321"
Forces replacement
```

**Bingo.** Your VM image was updated from June 17th to July 22nd, and Azure VMs are **immutable** when it comes to their base image. You can't just swap out the foundation of a running building—you need to tear it down and rebuild.

## The Cascade Effect 🌊

When your VM gets rebuilt, it triggers a domino effect:

1. **New VM = New Resource ID**
2. **Backup protection points to old VM**
3. **Terraform must delete old backup protection**
4. **Create new VM with new ID**
5. **Recreate backup protection for new VM**

This is why you're seeing those `Microsoft.RecoveryServices` deletion errors. Your service principal lacks the permission to clean up the old backup items.

## Why VMs Get Rebuilt (The Technical Reality)

Azure VMs are **immutable** for certain properties. Change any of these, and you're looking at a rebuild:

### 🔴 **Rebuild Triggers**
- **Image version** (your culprit)
- VM size changes
- Availability zone modifications
- OS disk encryption changes
- Network interface reassignment

### 🟢 **Safe Updates**
- Tags
- Extensions
- Data disks
- Network security groups
- Most configuration settings

## The Identity Plot Twist

Your plan also shows:
```hcl
identity {
  type: "SystemAssigned, UserAssigned" → "UserAssigned"
}
```

You're removing the system-assigned managed identity. While this doesn't force a rebuild by itself, it's another significant change happening simultaneously.

## The Resolution Strategy 🛠️

### Option 1: Embrace the Update (Recommended)
```json
// Add to your RBAC role
"Microsoft.RecoveryServices/vaults/backupFabrics/protectionContainers/protectedItems/delete"
```

**Why this is best:**
- Latest security patches
- Bug fixes and improvements
- Proper infrastructure hygiene

### Option 2: Pin the Image Version
```hcl
linux_image_version = "2025.06.17010625"  // Stay on old version
```

**Trade-offs:**
- No security updates
- Technical debt accumulation
- Delayed inevitable update

### Option 3: Temporary Workaround
Comment out backup protection temporarily:
```hcl
# resource "azurerm_backup_protected_vm" "protect_app_vm" {
#   // Temporarily disabled for image update
# }
```

## The Bigger Picture 🎯

This scenario illustrates a fundamental principle of Infrastructure as Code:

> **Immutable infrastructure isn't a bug—it's a feature.**

When you embrace rebuilds instead of in-place updates, you get:
- **Predictable deployments**
- **Consistent environments**
- **Reduced configuration drift**
- **Easier rollbacks**

## Key Takeaways 💡

1. **VM image updates = VM rebuilds** (by design)
2. **Plan for backup permission requirements**
3. **Immutable infrastructure is your friend**
4. **Regular image updates are security best practices**

## The Bottom Line

Your VM rebuild isn't a failure—it's Terraform ensuring your infrastructure stays consistent and secure. The real issue is a missing permission that prevents cleanup of the old backup protection.

Fix the permission, embrace the update, and your infrastructure will be stronger for it.

---

*Remember: In the world of cloud infrastructure, change is the only constant. Build your processes to embrace it, not fight it.*

**Tags:** `#Terraform` `#Azure` `#Infrastructure` `#DevOps` `#CloudSecurity`