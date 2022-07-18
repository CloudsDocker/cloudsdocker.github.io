 





Mock




MockResolver


/**
* A mock resolver offers an opportunity to resolve a mock from any instance that is
* provided to the {@link org.mockito.Mockito}-DSL. This mechanism can be used by
* frameworks that provide mocks that are implemented by Mockito but which are wrapped
* by other instances to enhance the proxy further.
*/
public interface MockResolver {



SpringBootMockResolver


/org/springframework/boot/spring-boot-test/2.5.9/spring-boot-test-2.5.9-sources.jar!/org/springframework/boot/test/mock/mockito/SpringBootMockResolver.java

public class SpringBootMockResolver implements MockResolver
A MockResolver for testing Spring Boot applications with Mockito.
Resolves mocks by returning the ultimate target object of the instance.


	@Override
	public Object resolve(Object instance) {
		return AopTestUtils.getUltimateTargetObject(instance);
	}




UltimateTargetObject
public static <T> T getUltimateTargetObject(Object  candidate)
Get the ultimate target object of the supplied candidate object, unwrapping not only a top-level proxy but also any number of nested proxies.
If the supplied candidate is a Spring proxy, the ultimate target of all nested proxies will be returned; otherwise, the candidate will be returned as is.





Mock vs Stubbing
Mocks and stubs are fake Java classes that replace these external dependencies. These fake classes are then instructed before the test starts to behave as you expect. More specifically:

A stub is a fake class that comes with preprogrammed return values. It’s injected into the class under test to give you absolute control over what’s being tested as input. A typical stub is a database connection that allows you to mimic any scenario without having a real database.
A mock is a fake class that can be examined after the test is finished for its interactions with the class under test. For example, you can ask it whether a method was called or how many times it was called. Typical mocks are classes with side effects that need to be examined, e.g. a class that sends emails or sends data to another external service.




Style
Mocks vs Stubs = Behavioral testing vs State testing

Principle
According to the principle of Test only one thing per test, there may be several stubs in one test, but generally there is only one mock.

Lifecycle
Test lifecycle with stubs:

Setup - Prepare object that is being tested and its stubs collaborators.
Exercise - Test the functionality.
Verify state - Use asserts to check object's state.
Teardown - Clean up resources.
Test lifecycle with mocks:

Setup data - Prepare object that is being tested.
Setup expectations - Prepare expectations in mock that is being used by primary object.
Exercise - Test the functionality.
Verify expectations - Verify that correct methods has been invoked in mock.
Verify state - Use asserts to check object's state.
Teardown - Clean up resources.


Stubbing in Mokito


//You can mock concrete classes, not just interfaces
  LinkedList mockedList = mock(LinkedList.class);
 
  //stubbing
  when(mockedList.get(0)).thenReturn("first");
  when(mockedList.get(1)).thenThrow(new RuntimeException());
 
  //following prints "first"
  System.out.println(mockedList.get(0));
 
  //following throws runtime exception
  System.out.println(mockedList.get(1));
 
  //following prints "null" because get(999) was not stubbed
  System.out.println(mockedList.get(999));
 
  //Although it is possible to verify a stubbed invocation, usually it's just redundant
  //If your code cares what get(0) returns, then something else breaks (often even before verify() gets executed).
  //If your code doesn't care what get(0) returns, then it should not be stubbed.
  verify(mockedList).get(0);


Stub practices
Stubbing can be overridden: for example common stubbing can go to fixture setup but the test methods can override it. Please note that overridding stubbing is a potential code smell that points out too much stubbing
Once stubbed, the method will always return a stubbed value, regardless of how many times it is called.
Last stubbing is more important - when you stubbed the same method with the same arguments many times. Other words: the order of stubbing matters but it is only meaningful rarely, e.g. when stubbing exactly the same method calls or sometimes when argument matchers are used, etc.




Spy
You can create spies of real objects. When you use the spy then the real methods are called (unless a method was stubbed).
Real spies should be used carefully and occasionally, for example when dealing with legacy code.
Spying on real objects can be associated with "partial mocking" concept. Before the release 1.8, Mockito spies were not real partial mocks. The reason was we thought partial mock is a code smell. At some point we found legitimate use cases for partial mocks (3rd party interfaces, interim refactoring of legacy code).

 List list = new LinkedList();
    List spy = spy(list);
 
    //optionally, you can stub out some methods:
    when(spy.size()).thenReturn(100);
 
    //using the spy calls *real* methods
    spy.add("one");
    spy.add("two");
 
    //prints "one" - the first element of a list
    System.out.println(spy.get(0));
 
    //size() method was stubbed - 100 is printed
    System.out.println(spy.size());
 
    //optionally, you can verify
    verify(spy).add("one");
    verify(spy).add("two");


 Mockito *does not* delegate calls to the passed real instance, instead it actually creates a copy of it. So if you keep the real instance and interact with it, don't expect the spied to be aware of those interaction and their effect on real instance state. The corollary is that when an *unstubbed* method is called *on the spy* but *not on the real instance*, you won't see any effects on the real instance.



Watch out for final methods. Mockito doesn't mock final methods so the bottom line is: when you spy on real objects + you try to stub a final method = trouble. Also you won't be able to verify those method as well.



RETURNS_SMART_NULLS
public static final Answer<Object > RETURNS_SMART_NULLS
Optional Answer to be used with mock(Class, Answer).
Answer can be used to define the return values of unstubbed invocations.
This implementation can be helpful when working with legacy code. Unstubbed methods often return null. If your code uses the object returned by an unstubbed call you get a NullPointerException. This implementation of Answer returns SmartNull instead of null. SmartNull gives nicer exception message than NPE because it points out the line where unstubbed method was called. You just click on the stack trace.
ReturnsSmartNulls first tries to return ordinary values (zeros, empty collections, empty string, etc.) then it tries to return SmartNull. If the return type is final then plain null is returned.
ReturnsSmartNulls will be probably the default return values strategy in Mockito 4.0.0
Example:

   Foo mock = mock(Foo.class, RETURNS_SMART_NULLS);

   //calling unstubbed method here:
   Stuff stuff = mock.getStuff();

   //using object returned by unstubbed call:
   stuff.doSomething();

   //Above doesn't yield NullPointerException this time!
   //Instead, SmartNullPointerException is thrown.
   //Exception's cause links to unstubbed mock.getStuff() - just click on the stack trace.

 





ArgumentCaptor


Mockito verifies argument values in natural java style: by using an equals() method. This is also the recommended way of matching arguments because it makes tests clean & simple. In some situations though, it is helpful to assert on certain arguments after the actual verification. For example:

ArgumentCaptor<Person> argument = ArgumentCaptor.forClass(Person.class);
    verify(mock).doSomething(argument.capture());
    assertEquals("John", argument.getValue().getName());

    Warning: it is recommended to use ArgumentCaptor with verification but not with stubbing. Using ArgumentCaptor with stubbing may decrease test readability because captor is created outside of assert (aka verify or 'then') block. Also it may reduce defect localization because if stubbed method was not called then no argument is captured.
In a way ArgumentCaptor is related to custom argument matchers (see javadoc for ArgumentMatcher class). Both techniques can be used for making sure certain arguments were passed to mocks. However, ArgumentCaptor may be a better fit if:
custom argument matcher is not likely to be reused
you just need it to assert on argument values to complete verification



ArgumentMatcher
Allows creating customised argument matchers. This API was changed in Mockito 2.1.0 in an effort to decouple Mockito from Hamcrest and reduce the risk of version incompatibility. Migration guide is included close to the bottom of this javadoc.


For non-trivial method arguments used in stubbing or verification, you have following options (in no particular order):
refactor the code so that the interactions with collaborators are easier to test with mocks. Perhaps it is possible to pass a different argument to the method so that mocking is easier? If stuff is hard to test it usually indicates the design could be better, so do refactor for testability!
don't match the argument strictly, just use one of the lenient argument matchers like ArgumentMatchers.notNull(). Some times it is better to have a simple test that works than a complicated test that seem to work.
implement equals() method in the objects that are used as arguments to mocks. Mockito naturally uses equals() for argument matching. Many times, this is option is clean and simple.


use ArgumentCaptor to capture the arguments and perform assertions on their state. Useful when you need to verify the arguments. Captor is not useful if you need argument matching for stubbing. Many times, this option leads to clean and readable tests with fine-grained validation of arguments.


use customized argument matchers by implementing ArgumentMatcher interface and passing the implementation to the ArgumentMatchers.argThat(org.mockito.ArgumentMatcher<T>) method. This option is useful if custom matcher is needed for stubbing and can be reused a lot. Note that ArgumentMatchers.argThat(org.mockito.ArgumentMatcher<T>) demonstrates NullPointerException auto-unboxing caveat.


use an instance of hamcrest matcher and pass it to MockitoHamcrest.argThat(org.hamcrest.Matcher) Useful if you already have a hamcrest matcher. Reuse and win! Note that MockitoHamcrest.argThat(org.hamcrest.Matcher) demonstrates NullPointerException auto-unboxing caveat.


Java 8 only - use a lambda in place of an ArgumentMatcher since ArgumentMatcher is effectively a functional interface. A lambda can be used with the ArgumentMatchers.argThat(org.mockito.ArgumentMatcher<T>) method.
Implementations of this interface can be used with ArgumentMatchers.argThat(org.mockito.ArgumentMatcher<T>) method. Use toString() method for description of the matcher - it is printed in verification errors.

class ListOfTwoElements implements ArgumentMatcher<List> {
     public boolean matches(List list) {
         return list.size() == 2;
     }
     public String toString() {
         //printed in verification errors
         return "[list of 2 elements]";
     }
 }

 List mock = mock(List.class);

 when(mock.addAll(argThat(new ListOfTwoElements()))).thenReturn(true);

 mock.addAll(Arrays.asList("one", "two"));

 verify(mock).addAll(argThat(new ListOfTwoElements()));
 
//To keep it readable you can extract method, e.g:
   verify(mock).addAll(argThat(new ListOfTwoElements()));
   //becomes
   verify(mock).addAll(listOfTwoElements());
 
//In Java 8 you can treat ArgumentMatcher as a functional interface and use a lambda, e.g.:
   verify(mock).addAll(argThat(list -> list.size() == 2));


verify
verify exact number of invocations
  //following two verifications work exactly the same - times(1) is used by default
  verify(mockedList).add("once");
  verify(mockedList, times(1)).add("once");

  //verification using atLeast()/atMost()
  verify(mockedList, atMostOnce()).add("once");
  verify(mockedList, atLeastOnce()).add("three times");
  verify(mockedList, atLeast(2)).add("three times");
  verify(mockedList, atMost(5)).add("three times");


verify void  method


You can use doThrow(), doAnswer(), doNothing(), doReturn() and doCallRealMethod() in place of the corresponding call with when(), for any method. It is necessary when you
stub void methods
stub methods on spy objects (see below)
stub the same method more than once, to change the behaviour of a mock in the middle of a test.

   doThrow(new RuntimeException()).when(mockedList).clear();

   //following throws RuntimeException:
   mockedList.clear();
 


verify order of calls
Using InOrder  for calls on. 

// A. Single mock whose methods must be invoked in a particular order
  List singleMock = mock(List.class);
 
  //using a single mock
  singleMock.add("was added first");
  singleMock.add("was added second");
 
  //create an inOrder verifier for a single mock
  InOrder inOrder = inOrder(singleMock);
 
  //following will make sure that add is first called with "was added first", then with "was added second"
  inOrder.verify(singleMock).add("was added first");
  inOrder.verify(singleMock).add("was added second");
 
  // B. Multiple mocks that must be used in a particular order
  List firstMock = mock(List.class);
  List secondMock = mock(List.class);
 
  //using mocks
  firstMock.add("was called first");
  secondMock.add("was called second");
 
  //create inOrder object passing any mocks that need to be verified in order
  InOrder inOrder = inOrder(firstMock, secondMock);
 
  //following will make sure that firstMock was called before secondMock
  inOrder.verify(firstMock).add("was called first");
  inOrder.verify(secondMock).add("was called second");








Mokito University 




Mokito Mocking details


26. Mocking details (Improved in 2.2.x)
Mockito offers API to inspect the details of a mock object. This API is useful for advanced users and mocking framework integrators.
    

//To identify whether a particular object is a mock or a spy:
    Mockito.mockingDetails(someObject).isMock();
    Mockito.mockingDetails(someObject).isSpy();
 
    //Getting details like type to mock or default answer:
    MockingDetails details = mockingDetails(mock);
    details.getMockCreationSettings().getTypeToMock();
    details.getMockCreationSettings().getDefaultAnswer();
 
    //Getting invocations and stubbings of the mock:
    MockingDetails details = mockingDetails(mock);
    details.getInvocations();
    details.getStubbings();
 
    //Printing all interactions (including stubbing, unused stubs)
    System.out.println(mockingDetails(mock).printInvocations());
  

For more information see javadoc for MockingDetails.





Errors 


Mock object different (or changed) which lead to test failed when run while test class, but run good when run individual test method.

As below screenshot, the left side is test method, right side is debug into the class under test

Solutions
remove @InjectMocks and build new SUT for @beforeEach




Todd Zhang > Mokito in depth > image2022-5-5_20-42-48.png





 
