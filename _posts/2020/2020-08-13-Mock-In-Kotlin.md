---
title: Mock in kotlin
date: 2020-08-13
tags:
 - Kotlin
 - Mock
layout: posts
---

# Argument Matching & Answers
For example, you have mocked DOC with call(arg: Int): Intfunction. You want to return 1 if argument is greater than 5 and -1 if it is less or equal to 5. This can be achieved by following construct:
every { mock.call(more(5)) } returns 1
every { mock.call(or(less(5), eq(5))) } returns -1


returnsMany specify a number of values that are used one by one i.e. first matched call returns first element, second — second element, e.t.c.
every { mock1.call(5) } returnsMany listOf(1, 2, 3)
You can achieve the same using andThen construct:
every { mock1.call(5) } returns 1 andThen 2 andThen 3



# Capture



CapturingSlot allows to capture only one value, so it is simpler to use.


```kotlin
val slot = slot<Int>()
val mock = mockk<Divider>()
every { mock.divide(capture(slot), any()) } returns 22
```


you can use a slot in an answer lambda:
every { 
  mock.divide(capture(slot), any()) 
} answers {
  slot.captured * 11
}
So mock.divide(5, 2) returns 55.


## Capture list
That is basically it. Working with MutableList is the same, just instead of a slot in capture function MutableList should be used.
val list = mutableList<Int>()
val mock = mockk<Divider>()
every { mock.divide(capture(list), any()) } returns 22

## Relaxed mocks

to skip specifying expected behavior and replies with some basic value alike null or 0. You can achieve in MockK by declaring relaxed mock.

val mock = mockk<Divider>(relaxed = true)

Then you can use it right away:

mock.divide(5, 2) // returns 0


# Spies
Spies give the possibility to set expected behavior and do behavior verification while still executing original methods of an object.

class Adder {
    fun magnify(a: Int) = a

    fun add(a: Int, b: Int) = a + magnify(b)
}
We want to test the behavior of add function while mocking behavior of magnify function.
Let’s first create a spy:
val spy = spyk(Adder())

Here we create object Adder() and build a spy on top of it. Building a spy actually means creating a special empty object of the same type and copying all the fields.
Now we can use it, as if it was regular Adder() object.
assertEquals(9, spy.add(4, 5))
This checks that original method is called.
Besides that, we can define spy behavior by putting it to every block:
every { spy.magnify(any()) } answers { firstArg<Int>() * 2 }


After that, behavior of add has changed because it was dependent on magnify:
assertEquals(14, spy.add(4, 5))


# Annotations
The library supports annotations @MockK, @SpyK and @RelxedMockK, which can be used as a simpler way to create mocks, spies, and relaxed mocks correspondingly.
```kotlin
class Test {
    @MockK
    lateinit var doc1: Dependency1

    @RelaxedMockK
    lateinit var doc2: Dependency2

    @SpyK
    val doc3 = Dependency3()

    @Before
    fun setUp() = MockKAnnotations.init(this)

    @Test
    fun calculateAddsValues1() {
        every { doc1.call().add(any()) } returns 5
        every { doc2.value2 } returns "6"
        every { doc3.sub(any()) } returns 7

        val sut = SystemUnderTest(doc1)

        assertEquals(11, sut.calculate())
    }
}
```
The important part here is MockKAnnotations.init(this) call which is executed at @Before phase. When it is executed all annotated properties are substituted with corresponding objects: mocks, spies and relaxed mocks.


# Mockito for Java

Mockito provides several methods to create mock objects:

Using the static mock() method.

Using the @Mock annotation.

If you use the @Mock annotation, you must trigger the initialization of the annotated fields. The MockitoRule does this by calling the static method MockitoAnnotations.initMocks(this). 




Hope this help!

--End--
