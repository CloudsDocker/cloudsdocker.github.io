---
title: The Great Migration -- Moving Azure Web App and App Service Plan Across Subscriptions
header:
    image: /assets/images/refind-java-SOLID-principles.jpg
date: 2024-11-30
tags:
- Networking
- TraceRoute
- Network Diagnostics

permalink: /blogs/tech/en/move-azure-resources-to-other-subscriptions
layout: single
category: tech
---
> A younger brother knows his older brother better than anyone else.


# The Great Migration: Moving Azure Web App and App Service Plan Across Subscriptions

## A Tale of Two Subscriptions

Picture this: It's Friday afternoon, and you've just received an urgent request to move a production web application to a different subscription. "Should be simple," you think, clicking through the Azure portal. But then you hit your first error message - something about hosting relationships and resource groups. Suddenly, what seemed like a straightforward task turns into a detective story, hunting down resource dependencies and unraveling the mysteries of Azure resource relationships.

Don't worry - you're not alone. Many Azure administrators have found themselves in this exact situation, staring at cryptic error messages about resource moves and hosting relationships. This guide will help you navigate these waters safely, turning what could be a weekend-long headache into a smooth sailing operation.

## Why This Guide Exists

Moving Azure resources across subscriptions is like moving to a new house - it's not just about picking up your stuff and going. You need to:
- Make sure all your belongings (resources) are properly packed (configured)
- Ensure related items (dependent resources) stay together
- Have your new house (destination subscription) ready before you move

This guide specifically focuses on moving Web Apps and their App Service Plans - a common scenario that comes with its own set of challenges and requirements.

## What You'll Learn

- Why Web Apps and App Service Plans need to stay together
- How to identify where your resources currently live
- Step-by-step process for a successful cross-subscription move
- Common pitfalls and how to avoid them

## Real-World Scenario

Let's follow a real example where we needed to move:
- A Web App (KeepItFresh)
- An App Service Plan (ASP-msdocspythonwebappquickstart-85e1)
From one subscription to another, while dealing with split resource groups and maintaining all functionality.

## Understanding Resource Locations

First, we need to verify where our resources currently reside. Use these Azure CLI commands:

```bash
# Check Web App location
az webapp show --name "KeepItFresh" --query "[resourceGroup, location]" --resource-group msdocs-python-webapp-quickstart

# Check App Service Plan location
az appservice plan show --name "ASP-msdocspythonwebappquickstart-85e1" --query "[resourceGroup, location]" --resource-group KeepItFresh_group
```

## Step 1: Consolidate Resources

Before moving resources across subscriptions, Web App and App Service Plan must be in the same resource group. This is a critical step - if they're in different resource groups, the cross-subscription move will fail.

```bash
# Move App Service Plan to the same resource group as Web App
az resource move \
  --ids "/subscriptions/source-subscription-id/resourceGroups/KeepItFresh_group/providers/Microsoft.Web/serverFarms/ASP-msdocspythonwebappquickstart-85e1" \
  --destination-group "msdocs-python-webapp-quickstart"
```

### Why This Step is Important

- Azure requires Web Apps and their associated App Service Plans to be in the same resource group for cross-subscription moves
- If they're in different resource groups, you'll get validation errors
- This maintains the service dependency relationship during the move

## Step 2: Create Destination Resource Group

Before moving resources, ensure the destination resource group exists in the target subscription:

```bash
# Switch to destination subscription
az account set --subscription "destination-subscription-id"

# Create resource group in the same region as source resources
az group create --name "rg-fresh-food" --location "Australia East"
```

## Step 3: Move Resources Together

Once both resources are properly aligned and the destination is prepared, move them together:

```bash
az resource move \
  --ids \
  "/subscriptions/source-subscription-id/resourceGroups/source-resource-group/providers/Microsoft.Web/sites/KeepItFresh" \
  "/subscriptions/source-subscription-id/resourceGroups/source-resource-group/providers/Microsoft.Web/serverFarms/ASP-msdocspythonwebappquickstart-85e1" \
  --destination-subscription "destination-subscription-id" \
  --destination-group "rg-fresh-food"
```

## Important Notes

1. Web Apps and their App Service Plans should be moved together - they're like a parent and child, inseparable
2. The destination resource group must exist before attempting the move - you need a new home ready before moving
3. Resources must be in the same resource group before moving across subscriptions - keep the family together
4. Keep the same region/location for the destination resource group as the source resources - maintain performance and compliance

## Common Issues and Solutions

1. **ResourceGroupNotFound**: Create the destination resource group before attempting the move
2. **Resources Being Moved**: Wait for any ongoing move operations to complete before attempting new moves
3. **Resource Move Validation Failed**: Ensure both App Service Plan and Web App are in the same resource group before attempting cross-subscription move
4. **Cannot Move Resource**: Double-check that both Web App and App Service Plan are selected for the move operation

## Best Practices

1. Always verify resource locations before attempting moves
2. Ensure resources are in the same resource group before cross-subscription moves
3. Keep all dependent resources together during moves
4. Document the current configuration before making any changes
5. Plan your moves during off-peak hours to minimize potential impact

## Conclusion

Moving Azure resources across subscriptions doesn't have to be a scary process. By understanding the relationship between Web Apps and App Service Plans, and following this guide's steps, you can ensure a smooth migration without any unexpected surprises.

Remember: Like any good relationship, Web Apps and their App Service Plans work best when they stay together. Keep them in the same resource group, move them together, and your cross-subscription migration will be a success story rather than a cautionary tale.

Happy moving!

--HTH--