---
header:
    image: /assets/images/hd_jupiter.png
title:  Untold stories for Jupiter, any differences JUnit 5 vs Junit 4
date: 2022-02-22
tags:
 - JUnit
 - Java
 
permalink: /blogs/tech/en/JUpiter_Junit5_vs_Junit4
layout: single
category: tech
---

> Don't tell people your plans. Just show them your results!


# JUnit5 (Jupiter) 
As you know, Junit 5 with the goal of supporting new features in Java 8 and above, as well as enabling many different styles of testing.


## Components of Jupiter
Unlike previous versions of JUnit, JUnit 5 is composed of several different modules from three different sub-projects.

`JUnit 5 = JUnit Platform + JUnit Jupiter + JUnit Vintage`



### Junit Platform
The JUnit Platform serves as a foundation for launching testing frameworks on the JVM. It also defines the TestEngine API for developing a testing framework that runs on the platform.


### JUnit Jupiter 
is the combination of the new programming model and extension model for writing tests and extensions in JUnit 5. The Jupiter sub-project provides a TestEngine for running Jupiter based tests on the platform.


### JUnit Vintage 
This is mainly for backwards compatibility, it provides a TestEngine for running JUnit 3 and JUnit 4 based tests on the platform. It requires JUnit 4.12 or later to be present on the class path or module path.


## Talk is cheap, let's see some code


Sample Jupiter test
```java
class MyFirstJUnitJupiterTests {
 
    private final Calculator calculator = new Calculator();
 
    @Test
    void addition() {
        assertEquals(2, calculator.add(1, 1));
    }
 
}
```

### @ParameterizedTest


```java
@ParameterizedTest
    @ValueSource(strings={"hello","world","keyboard"})
    void dummyMethod1(String input) {
        assertEquals(5,inst.dummyMethod1(input));
    }
```

### @RepeatedTest

```java
    @RepeatedTest(5)
    void dummyTets2(){
        assertEquals(3,inst.dummyMethod1("abc"));
    }
```

So you'll see those results in detailed lines, as below screenshot:

![](/assets/images/jupiter_test_result.png)


## Class and method visibility


Test classes, test methods, and lifecycle methods are not required to be public, but they must not be private.

It is generally recommended to omit the public modifier for test classes, test methods, and lifecycle methods unless there is a technical reason for doing so



# Annotations: @Test, @Testable , and @TestFactory


## @Testable 
It is used to signal to IDEs and tooling vendors that the annotated or meta-annotated element is testable.


### Motivation for @Testable

Some clients of the JUnit Platform, notably IDEs such as IntelliJ IDEA, operate only on sources for test discovery. Thus, they cannot use the full runtime discovery mechanism of the JUnit Platform since it relies on compiled classes. @Testable therefore serves as an alternative mechanism for IDEs to discover potential tests by analyzing the source code only.
Common Use Cases


## TestEngine
public interface TestEngine
A TestEngine facilitates discovery and execution of tests for a particular programming model.

For example, JUnit provides a TestEngine that discovers and executes tests written using the JUnit Jupiter programming model.


In order to facilitate test discovery within IDEs and tools prior to launching the JUnit Platform, TestEngine implementations are encouraged to make use of the @Testable annotation. For example, the @Test and @TestFactory annotations in JUnit Jupiter are meta-annotated with @Testable.



## Differences among junit 4 and Jupiter


For check there are differecnes among junit 4 and Jupiter


# Assert Assertions
A set of assertion methods useful for writing tests.	Assertions is a collection of utility methods that support asserting conditions in tests.
From Assert.assertEquals(String message, Object expected, Object actual) to Assertions.assertEquals(Object expected, Object actual, String message).


# Assertions


we can now use lambdas in assertions:

```java
@Test
void lambdaExpressions() {
    assertTrue(Stream.of(1, 2, 3)
      .stream()
      .mapToInt(i -> i)
      .sum() > 5, () -> "Sum should be greater than 5");
}
```


one advantage of using the lambda expression for the assertion message is that `it's lazily evaluated, which can save time and resources` if the message construction is expensive.



It's also now possible to group assertions with assertAll(), which will report any failed assertions within the group with a MultipleFailuresError:

```java
 @Test
 void groupAssertions() {
     int[] numbers = {0, 1, 2, 3, 4};
     assertAll("numbers",
         () -> assertEquals(numbers[0], 1),
         () -> assertEquals(numbers[3], 3),
         () -> assertEquals(numbers[4], 1)
     );
 }
```


# Assumptions

Assumptions are used to run tests only if certain conditions are met. This is typically used for external conditions that are required for the test to run properly, but which aren't directly related to whatever is being tested.

We can declare an assumption with assumeTrue(), assumeFalse(), and assumingThat():


If an assumption fails, a TestAbortedException is thrown and the test is simply skipped.

Assumptions also understand lambda expressions.
```java
@Test
void trueAssumption() {
    assumeTrue(5 > 1);
    assertEquals(5 + 2, 7);
}
 
@Test
void falseAssumption() {
    assumeFalse(5 < 1);
    assertEquals(5 + 2, 7);
}
 
@Test
void assumptionThat() {
    String someString = "Just a string";
    assumingThat(
        someString.equals("Just a string"),
        () -> assertEquals(2 + 2, 4)
    );
}
```

## Exception Testing
```java

@Test
void shouldThrowException() {
    Throwable exception = assertThrows(UnsupportedOperationException.class, () -> {
      throw new UnsupportedOperationException("Not supported");
    });
    assertEquals(exception.getMessage(), "Not supported");
}
 
@Test
void assertThrowsException() {
    String str = null;
    assertThrows(IllegalArgumentException.class, () -> {
      Integer.valueOf(str);
    });
}

```

# Better assertions, using matchers.
## Hamcrest (For matchers)

> Do you know, Hamcrest is coined by rearrange characters of `Matchers`

There are rich and more readable API for matchers of Hamcrest.

The error message of Hamcrest is more understandable. You can get why your test fails easily. However, the error message of assertTrue is hard to understand.


```java
@Test
public void shouldGetAvailableTaxes() throws Exception {
    List actual = TaxCalculator.AVAILABLE_TAXES;
    //JUnit assertions
    assertEquals(Arrays.asList(“KDV”, “OTV”, “MTV”), actual);
    assertTrue(actual.contains(“KDV”));
    assertTrue(!actual.contains(“KDM”));
    assertEquals(3, actual.size());
 
    //Hamcrest matcher
    assertThat(actual, containsInAnyOrder(“KDV”, “OTV”, “MTV”));
    assertThat(actual, not(contains(“KDV”, “MTV”, “OTV”)));
    assertThat(actual, contains(“KDV”, “OTV”, “MTV”));
    assertThat(actual, hasItems(“KDV”, “OTV”));
    assertThat(actual, hasItem(“MTV”));
    assertThat(actual, hasSize(3));
    assertThat(actual, instanceOf(List.class));
    assertThat(actual, everyItem(notNullValue(String.class)));
    assertThat(actual, everyItem(not(isEmptyOrNullString())));
}
```


To use it, you must add following to `pom.xml`

```xml
<dependency>
  <groupId>org.hamcrest</groupId>
  <artifactId>hamcrest-library</artifactId>
  <version>2.2</version>
  <scope>test</scope>
</dependency>
```











--End--



