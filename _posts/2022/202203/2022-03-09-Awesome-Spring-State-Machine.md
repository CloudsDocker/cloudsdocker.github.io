---
header:
    image: /assets/images/hd_state_machine.png
title:  Everything you'd know about state machine for interviews
date: 2022-03-09
tags:
 - Spring
 - Java
 - StateMachine
 
permalink: /blogs/tech/en/awesome_state_machine_in_spring
layout: single
category: tech
---

> Less expecting, more accepting.


# State Machine Summary


## Why State machine
State machines are powerful because behaviour is always guaranteed to be consistent, making it relatively easy to debug. 

 This is because operational `rules are written in stone` when the machine is started.

## Interaction with state machine

 You can interact with the state machine by sending an event, listening for changes or simply request a current state.

# Persist StateMachine
One key point is you have to persist `StateMachineContext` rather than `StateMachine`

## StateMachinePersister vs StateMachinePersist

For `StateMachinePersist`, it handling serialization logic of a StateMachineContext. You need to implement at least two methods, `read` and `write`

While for `StateMachinePersister`, persisting and restoring a StateMachine from a persistent storage.

One of it's implementation, `DefaultStateMachinePersister` which just a default wrapper of `AbstractStateMachinePersister`,. It's Constructor accept one instance of `StateMachinePersist`, and for the method `persiste` and `restore`, they are actually invoke `read` and `write` from underlying StateMachinePersist.

--End--



