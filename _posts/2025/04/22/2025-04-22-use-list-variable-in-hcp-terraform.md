---
header:
    image: /assets/images/hd_mvn_skip_tests.png
title:  Configuring List Variables in HCP Terraform Cloud
date: 2025-04-22
tags:
    - tech
    - DevOps
    - Enterprise Security
    - GitHub
    - SAML SSO 
permalink: /blogs/tech/en/use-list-variable-in-hcp-terraform
layout: single
category: tech
---
# Configuring List Variables in HCP Terraform Cloud

## Issue
When setting list-type variables in HCP Terraform Cloud, you may encounter the following error:
```
Error: Invalid value for input variable
The given value is not suitable for var.subnet_appgw_address: list of string required.
```

## Solution

### 1. Variable Definition in Terraform
The variable is correctly defined in `variables.tf`:
```terraform
variable "subnet_appgw_address" {
  description = "Address prefixes for the application gateway subnet"
  type        = list(string)
  default     = ["10.148.36.0/24"]
}
```

### 2. Correct Configuration in HCP Terraform Cloud
To properly set list variables in HCP Terraform Cloud:

1. Navigate to your workspace variables
2. Add/Edit the variable `subnet_appgw_address`
3. Enter the value: `["10.148.36.0/24"]`
4. **Important**: Check the "HCL" checkbox
5. Save the variable

### Common Mistakes to Avoid
- Don't use escaped quotes (`\"`)
- Don't wrap the entire value in additional quotes
- Don't forget to check the "HCL" checkbox

### Example
✅ Correct:
```hcl
["10.148.36.0/24"]
```

❌ Incorrect:
```
"[\"10.148.36.0/24\"]"
```

## Additional Notes
- This approach applies to all list-type variables in HCP Terraform Cloud
- The HCL checkbox tells HCP to parse the input as HCL syntax rather than a plain string
- Always validate the variable type matches your Terraform configuration
