---
title: io_mockk_MockKException__no_answer_found_for
header:
    image: /assets/images/io-mockk-MockKException--no-answer-found-for.jpg
date: 2023-04-22
tags:
- ssh
- devops
- automation

permalink: /blogs/tech/en/io-mockk-MockKException-no-answer-found-for
layout: single
category: tech
---
> A young idler, an old beggar. - William Shakespeare

## How to fix `io.mockk.MockKException: no answer found for: DeliveryStatusChangeEvent(#1).getOrder()`

The `io.mockk.MockKException: no answer found for...` error message typically occurs when MockK, a mocking library for Kotlin, cannot find a suitable response for a method invocation on a mocked object.

In your specific case, the error message indicates that there is no answer defined for the `getOrder()` method call on the `DeliveryStatusChangeEvent` object.

To fix this error, you need to define a suitable response for the `getOrder()` method call on the mocked `DeliveryStatusChangeEvent` object.

Here is an example of how to define a response using the `every` function from MockK:

```kotlin
val DeliveryStatusChangeEvent = mockk<DeliveryStatusChangeEvent>()

// Define a response for the getOrder() method
every { DeliveryStatusChangeEvent.getOrder() } returns someOrder

// Call the method and verify the response
val order = DeliveryStatusChangeEvent.getOrder()
assertEquals(someOrder, order)
```

In this example, the every function defines a response for the getOrder() method call on the mocked OrderFulfillmentStatusChangeEvent object. The returns function specifies the response to return when the getOrder() method is called.

You should replace someOrder with a real instance of the Order class that you want to use for testing. This way, when you call the getOrder() method on the mocked OrderFulfillmentStatusChangeEvent object, it will return the Order instance that you defined as the response.

By defining a suitable response for the method call, you should be able to resolve the io.mockk.MockKException: no answer found for... error and continue testing your code.

--HTH--
