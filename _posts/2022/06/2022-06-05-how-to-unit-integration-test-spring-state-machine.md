---
header:
    image: /assets/images/hd_test_spring_state_machine.png
title:  How to build unit/integration tests for Spring State Machine
date: 2022-06-05
tags:
 - SpringFramework
 - Java
 - SpringBoot
 - StateMachine
permalink: /blogs/tech/en/how-to-unit-integration-test-spring-state-machine
layout: single
category: tech
---
> Get busy living or get busy dying.

# Summary

To run integration  and unit  test Spring State Machine, you can leverage Spring State Machine's **StateMachineTestPlan** and *StateMachineTestPlanBuilder*. 

Firstly, let's take a look at one full example for this testing

# Code sample

```java
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.statemachine.StateMachine;
import org.springframework.statemachine.config.EnableStateMachineFactory;
import org.springframework.statemachine.config.StateMachineFactory;
import org.springframework.statemachine.test.StateMachineTestPlan;
import org.springframework.statemachine.test.StateMachineTestPlanBuilder;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.junit4.SpringRunner;
 
 
@RunWith(SpringRunner.class)
@SpringBootTest(classes = {YourOwnStateMachineConfig.class},
        properties = "spring.main.allow-bean-definition-overriding=true")
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_EACH_TEST_METHOD)
@EnableStateMachineFactory(contextEvents = false)
public class TestStateMachine {
 
    @MockBean
    private StateMachineLoggingListener stateMachineLoggingListener;
 
    @Autowired
    private StateMachineFactory<YourStateDto, YourEventDto> stateMachineFactory;
 
    private StateMachine<YourStateDto, YourEventDto> stateMachine;
 
    @Before
    public void setup() throws Exception {
        stateMachine = stateMachineFactory.getStateMachine();
        // plan don't know how to wait if machine is started
        // automatically so wait here.
        for (int i = 0; i < 10; i++) {
            if (stateMachine.getState() != null) {
                break;
            } else {
                Thread.sleep(200);
            }
        }
    }
 
    @Test
    public void shouldMoveForwardInGoodPath() throws Exception {
        StateMachineTestPlan<YourStateDto, YourEventDto> plan =
                StateMachineTestPlanBuilder.<YourStateDto, YourEventDto>builder()
                        .stateMachine(stateMachine)
                        .step()
                        .expectState(STATE_INIT)
                        .and()
                        .step()
                        .sendEvent(EVENT_2ND_STEP)
                        .sendEvent(EVENT_3RD_STEP)
                        .sendEvent(EVENT_4TH_STEP)
                        .expectState(STATE_COMPLETED)
                        .and()
                        .build();
        plan.test();
    }
 
 
 
    @Test
    public void shouldMoveToEndInTheMiddleOfFlow() throws Exception {
        StateMachineTestPlan<YourStateDto, YourEventDto> plan =
                StateMachineTestPlanBuilder.<YourStateDto, YourEventDto>builder()
                        .stateMachine(stateMachine)
                        .step()
                        .expectState(STATE_INIT)
                        .and()
                        .step()
                        .sendEvent(EVENT_2ND_STEP)
                        .expectState(STATE_MIDDLE)
                        .and()
                        .step()
                        .sendEvent(EVENT_CLOSE_STEP)
                        .expectState(STATE_COMPLETED)
                        .and()
                        .build();
        plan.test();
    }
 
    @Test
    public void shouldRejectWorkFlow() throws Exception {
        StateMachineTestPlan<YourStateDto, YourEventDto> plan =
                StateMachineTestPlanBuilder.<YourStateDto, YourEventDto>builder()
                        .stateMachine(stateMachine)
                        .step()
                        .sendEvent(EVENT_2ND_STEP)
                        .sendEvent(EVENT_3RD_STEP)
                        .sendEvent(EVENT_4TH_STEP)
                        .expectState(STATE_MIDDLE)
                        .and()
                        .step()
                        .sendEvent(PA_E_REJECT_SOA)
                        .expectState(STATE_MIDDLE_MORE)
                        .and()
                        .step()
                        .sendEvent(EVENT_4TH_STEP)
                        .sendEvent(EVENT_5TH_STEP)
                        .expectState(STATE_REJECTED)
                        .and()
                        .build();
        plan.test();
    }
}
```

# Instructions
To test a statemachine, firstly you'd using following annotations:
 - @RunWith(SpringRunner.class) : to run this test with Spring integrated Junit runner 
 - @SpringBootTest(classes = {YourOwnStateMachineConfig.class} : this shoudl assign the Java class with @Configuraion and defines your state machine state/transition/events.

Secondly, you'd autowire a bean about the `StateMahineFactory` which will be created *automatically* .

@Autowired
    private StateMachineFactory<YourStateDto, YourEventDto> stateMachineFactory;

This StateMachineFactory is one *ObjectStateMachineFactory* within package org.springframework.statemachine.config;

This is created during `afterPropertiesSet` method within StateMachineFactoryConfiguration. 

Details as:
org\springframework\statemachine\config\configuration\StateMachineFactoryConfiguration.java

So it means if you put Spring StateMachine library/binary into your class path (e.g. include spring state machine in pom.xml), it will be executed automatically. 

As below code snippet

```java
@Override
		public void afterPropertiesSet() throws Exception {
```

-HTH-
