---
title: When Your Retry Mechanism Doesn't Retry - A Tale of String Matching Gone Wrong
header:
    image: /assets/images/compile-error-java-kotlin-coexist-project-in-intellij.jpg
date: 2024-12-16
tags:
- Python
- Coding

permalink: /blogs/tech/en/When_Your_Retry_Mechanism_Doesnt_Retry_A_Tale_of_String_Matching_Gone_Wrong
layout: single
category: tech
---
> The biggest room in the world is the room for improvement.
— Helmut Schmidt

# When Your Retry Mechanism Doesn't Retry: A Tale of String Matching Gone Wrong

It was 4:47 AM when my phone buzzed with yet another alert. Bleary-eyed, I reached for it, expecting another routine notification. Instead, I found myself staring at a cascade of failed Airflow tasks. The error message was painfully familiar: "ThrottlingException: Rate exceeded." What caught my attention wasn't the error itselfâ€”rate limits are a fact of life when working with cloud services. No, what bothered me was that our retry mechanism, specifically designed to handle these situations, hadn't kicked in.

"But we have retry logic for this exact scenario," I muttered to myself, now fully awake. This began a fascinating journey into the subtle ways string matching can fail us, and how a few lines of code can make the difference between a resilient system and a fragile one.

## The Mystery

Our ECS (Elastic Container Service) tasks were failing with throttling errors, despite having what appeared to be perfectly good retry logic:

```python
RETRIABLE_EXCEPTIONS = {
    "Timeout waiting for network interface provisioning to complete",
    "Rate exceeded"
}

try:
    return super().execute(context)
except (AirflowException, WaiterError) as e:
    for exception_message in RETRIABLE_EXCEPTIONS:
        if exception_message in str(e):
            time.sleep(self.retry_delay.total_seconds())
            return super().execute(context)
        else:
            raise
```

The actual error message we were getting was:
```
Waiter TasksStopped failed: An error occurred (ThrottlingException): Rate exceeded
```

Can you spot the issue? It's subtle, but its impact was significant.

## The Bug: A Tale of Two Strings

The problem lay in two critical misconceptions:

1. **Partial String Matching**: While our `RETRIABLE_EXCEPTIONS` set included "Rate exceeded", the actual error message contained this string buried within a longer message. Our code was looking for an exact match when it should have been looking for a substring.

2. **Premature Raising**: The `else: raise` statement inside our `for` loop meant that if the first exception message didn't match, we'd raise immediately without checking other potential matches. It was like having a bouncer who checks only the first name on the guest list before turning people away.

## The Solution: Embracing Flexibility

Here's how we fixed it:

```python
try:
    return super().execute(context)
except (AirflowException, WaiterError) as e:
    error_message = str(e)
    should_retry = any(exc_msg in error_message for exc_msg in RETRIABLE_EXCEPTIONS)
    
    if should_retry:
        self.log.info(f"Caught retriable error: {error_message}. Attempting retry after delay.")
        time.sleep(self.retry_delay.total_seconds())
        return super().execute(context)
    
    self.log.error(f"Caught non-retriable error: {error_message}")
    raise
```

This solution introduces several improvements:
- Uses `any()` to check all possible matches before deciding whether to retry
- Moves the retry logic outside the loop
- Adds logging to help diagnose issues
- Properly handles the full error message string

## Making It Production-Ready

For a truly robust solution, we extended this further:

```python
RETRIABLE_EXCEPTIONS = {
    "Timeout waiting for network interface provisioning to complete",
    "Rate exceeded",
    "ThrottlingException"  # Added to catch the exception type
}

MAX_RETRIES = 3
BASE_DELAY = 30  # seconds

try:
    return super().execute(context)
except (AirflowException, WaiterError) as e:
    error_message = str(e)
    should_retry = any(exc_msg in error_message for exc_msg in RETRIABLE_EXCEPTIONS)
    
    if should_retry:
        for attempt in range(MAX_RETRIES):
            try:
                delay = BASE_DELAY * (2 ** attempt)  # Exponential backoff
                self.log.info(f"Retry attempt {attempt + 1}/{MAX_RETRIES} after {delay} seconds")
                time.sleep(delay)
                return super().execute(context)
            except (AirflowException, WaiterError) as retry_e:
                if attempt == MAX_RETRIES - 1:  # Last attempt failed
                    self.log.error(f"All retry attempts failed. Last error: {str(retry_e)}")
                    raise
                continue
    
    self.log.error(f"Caught non-retriable error: {error_message}")
    raise
```

This production version includes:
- Exponential backoff to prevent overwhelming the service
- Multiple retry attempts
- Comprehensive logging
- Graceful handling of nested exceptions

## Lessons Learned

1. **Test With Real Error Messages**: Unit tests with manufactured error messages might not catch subtle string matching issues. Always test with real error messages from production.

2. **Log Everything**: Detailed logging helped us understand why our retry mechanism wasn't triggering. Without logs, we would have been flying blind.

3. **Think in Patterns**: Rather than matching exact strings, think about patterns of errors. In our case, we needed to match substrings rather than exact strings.

4. **Fail Gracefully**: A retry mechanism should degrade gracefully, with proper logging and multiple attempts before giving up.

## The Happy Ending

After deploying these changes, our 4 AM alerts became much less frequent. The system now handles rate limiting gracefully, automatically retrying with exponential backoff when needed. Our on-call engineers are sleeping better, and our services are more resilient.

This experience taught us that even simple string matching can have complex implications for system reliability. Sometimes the most subtle bugs have the biggest impact on system stability.

Remember: in the world of distributed systems, it's not about avoiding failuresâ€”it's about handling them gracefully.

Thank you for reading, and happy coding!

--HTH--
