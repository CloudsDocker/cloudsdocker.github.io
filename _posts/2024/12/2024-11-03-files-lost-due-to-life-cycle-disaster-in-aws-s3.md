---
title: Avoiding Data Loss - S3 Lifecycle Rules During Terraform Version Migrations
header:
    image: /assets/images/Understanding_Backpropagation_in_Neural_Networks.jpg
date: 2024-12-03
tags:
- AWS
- S3

permalink: /blogs/tech/en/files-lost-due-to-life-cycle-disaster-in-aws-s3
layout: single
category: tech
---
> Your past is a lesson. Not a life sentence.
> Forgive yourself and focus on the future.
> -Mel Robbins

# Avoiding Data Loss: S3 Lifecycle Rules During Terraform Version Migrations

## The Incident

Recently, we encountered a significant issue during a Terraform version upgrade from 0.12 to 0.13 that resulted in unexpected data loss in AWS S3. The incident occurred when migrating S3 bucket lifecycle rules, specifically relating to the change in syntax for prefix filters. This post examines what happened, why it happened, and how to prevent similar issues.

## Background

Our S3 bucket had three lifecycle rules:
1. Archive files to Glacier after 30 days
2. Expire [Directory-A] files after 1054 days
3. Expire [Directory-B] files after 14 days

### Original Configuration (Terraform 0.12)
```hcl
lifecycle_rule:
  - id: "archive"
    enabled: true
    transition:
      - days: 30
        storage_class: "GLACIER"
  - id: "expire_objects_dir_a"
    enabled: true
    prefix: "[Directory-A]/"    # Old syntax
    expiration:
      days: 1054
  - id: "expire_objects_dir_b"
    enabled: true
    prefix: "[Directory-B]/" # Old syntax
    expiration:
      days: 14
```

### New Configuration (Terraform 0.13)
```hcl
lifecycle_rule:
  - id: "archive"
    enabled: true
    transition:
      - days: 30
        storage_class: "GLACIER"
  - id: "expire_objects_dir_a"
    enabled: true
    filter:           # New syntax
      prefix: "[Directory-A]/"
    expiration:
      days: 1054
  - id: "expire_objects_dir_b"
    enabled: true
    filter:           # New syntax
      prefix: "[Directory-B]/"
    expiration:
      days: 14
```

## What Went Wrong

During the migration, a critical issue occurred:
1. The prefix filter syntax changed from direct notation to a filter block
2. During the transition, the filter configuration was temporarily missing
3. Without prefix filters, the rules applied globally to the entire bucket
4. The shortest expiration rule (14 days) was applied to all files
5. Result: All files older than 14 days were deleted, including archived Glacier files

## Impact

1. Loss of archived data in Glacier storage
2. Unintended deletion of files outside the intended prefixes
3. Potential business impact due to data loss
4. Time and resources spent on incident investigation and recovery

## Root Cause Analysis

The root cause was a combination of factors:
1. Syntax changes in Terraform version upgrade
2. Missing validation of lifecycle rule changes
3. Insufficient review of terraform plan output
4. No staged rollout of version upgrade

## Prevention Measures

### 1. Pre-Migration Steps
- Document all existing lifecycle rules
- Take inventory of critical data
- Create backup of critical configurations
- Test migration in a non-production environment

### 2. During Migration
- Use terraform plan with extra scrutiny on lifecycle rules
- Use `-target` flag for gradual rollout
- Implement changes in stages
- Verify each rule's scope after application

### 3. Post-Migration Validation
```bash
# Verify lifecycle rules
aws s3api get-bucket-lifecycle-configuration --bucket your-bucket-name

# Check prefix filters are correctly applied
aws s3api list-objects-v2 --bucket your-bucket-name --prefix "[Directory-A]/" --query 'Contents[].Key'
```

### 4. Best Practices
- Implement version control for terraform configurations
- Use terraform workspaces for environment separation
- Create automated tests for infrastructure changes
- Maintain detailed documentation of S3 bucket policies

## Recovery Steps If Incident Occurs

1. Immediate Actions:
   - Disable problematic lifecycle rules
   - Document affected files and timeframes
   - Notify stakeholders

2. Recovery Process:
   - Restore from backups if available
   - Recreate data from source systems if possible
   - Verify data integrity after restoration

3. Post-Recovery:
   - Update documentation
   - Implement additional safeguards
   - Conduct thorough review of similar configurations

## Conclusion

This incident highlights the importance of careful planning and validation during infrastructure version upgrades. The key takeaways are:

1. Always review terraform plan output thoroughly
2. Implement gradual rollouts for version upgrades
3. Maintain comprehensive backup strategies
4. Test migrations in non-production environments
5. Document and verify all lifecycle rules before and after changes

Remember: S3 lifecycle rules are powerful tools but require careful management, especially during infrastructure changes. A systematic approach to changes and thorough validation can prevent unintended data loss.

--HTH--
