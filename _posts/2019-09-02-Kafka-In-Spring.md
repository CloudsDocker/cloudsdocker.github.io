---
title:  Kafka In Spring
layout: posts
---

Enable Kafka listener annotated endpoints that are created under the covers by a AbstractListenerContainerFactory. To be used on Configuration classes as follows:
   @Configuration
   @EnableKafka
   public class AppConfig {
   	@Bean
   	public ConcurrentKafkaListenerContainerFactory myKafkaListenerContainerFactory() {
   		ConcurrentKafkaListenerContainerFactory factory = new ConcurrentKafkaListenerContainerFactory();
   		factory.setConsumerFactory(consumerFactory());
   		factory.setConcurrency(4);
   		return factory;
   	}
   	// other @Bean definitions
   }
   
The KafkaListenerContainerFactory is responsible to create the listener container for a particular endpoint. Typical implementations, as the ConcurrentKafkaListenerContainerFactory used in the sample above, provides the necessary configuration options that are supported by the underlying MessageListenerContainer.
@EnableKafka enables detection of KafkaListener annotations on any Spring-managed bean in the container. For example, given a class MyService:
   package com.acme.foo;
  
   public class MyService {
   	@KafkaListener(containerFactory = "myKafkaListenerContainerFactory", topics = "myTopic")
   	public void process(String msg) {
   		// process incoming message
   	}
   }
   
The container factory to use is identified by the containerFactory attribute defining the name of the KafkaListenerContainerFactory bean to use. When none is set a KafkaListenerContainerFactory bean with name kafkaListenerContainerFactory is assumed to be present.
the following configuration would ensure that every time a message is received from topic "myQueue", MyService.process() is called with the content of the message:
   @Configuration
   @EnableKafka
   public class AppConfig {
   	@Bean
   	public MyService myService() {
   		return new MyService();
   	}
  
   	// Kafka infrastructure setup
   }
   
Alternatively, if MyService were annotated with @Component, the following configuration would ensure that its @KafkaListener annotated method is invoked with a matching incoming message:
   @Configuration
   @EnableKafka
   @ComponentScan(basePackages = "com.acme.foo")
   public class AppConfig {
   }
   
Note that the created containers are not registered with the application context but can be easily located for management purposes using the KafkaListenerEndpointRegistry.
Annotated methods can use a flexible signature; in particular, it is possible to use the Message abstraction and related annotations, see KafkaListener Javadoc for more details. For instance, the following would inject the content of the message and the kafka partition header:
   @KafkaListener(containerFactory = "myKafkaListenerContainerFactory", topics = "myTopic")
   public void process(String msg, @Header("kafka_partition") int partition) {
   	// process incoming message
   }
   
These features are abstracted by the MessageHandlerMethodFactory that is responsible to build the necessary invoker to process the annotated method. By default, DefaultMessageHandlerMethodFactory is used.
When more control is desired, a @Configuration class may implement KafkaListenerConfigurer. This allows access to the underlying KafkaListenerEndpointRegistrar instance. The following example demonstrates how to specify an explicit default KafkaListenerContainerFactory
   {
   	@code
   	@Configuration
   	@EnableKafka
   	public class AppConfig implements KafkaListenerConfigurer {
   		@Override
   		public void configureKafkaListeners(KafkaListenerEndpointRegistrar registrar) {
   			registrar.setContainerFactory(myKafkaListenerContainerFactory());
   		}
  
   		@Bean
   		public KafkaListenerContainerFactory<?, ?> myKafkaListenerContainerFactory() {
   			// factory settings
   		}
  
   		@Bean
   		public MyService myService() {
   			return new MyService();
   		}
   	}
   }
   
It is also possible to specify a custom KafkaListenerEndpointRegistry in case you need more control on the way the containers are created and managed. The example below also demonstrates how to customize the org.springframework.messaging.handler.annotation.support.DefaultMessageHandlerMethodFactory as well as how to supply a custom Validator so that payloads annotated with Validated are first validated against a custom Validator.
   {
   	@code
   	@Configuration
   	@EnableKafka
   	public class AppConfig implements KafkaListenerConfigurer {
   		@Override
   		public void configureKafkaListeners(KafkaListenerEndpointRegistrar registrar) {
   			registrar.setEndpointRegistry(myKafkaListenerEndpointRegistry());
   			registrar.setMessageHandlerMethodFactory(myMessageHandlerMethodFactory);
   			registrar.setValidator(new MyValidator());
   		}
  
   		@Bean
   		public KafkaListenerEndpointRegistry myKafkaListenerEndpointRegistry() {
   			// registry configuration
   		}
  
   		@Bean
   		public MessageHandlerMethodFactory myMessageHandlerMethodFactory() {
   			DefaultMessageHandlerMethodFactory factory = new DefaultMessageHandlerMethodFactory();
   			// factory configuration
   			return factory;
   		}
  
   		@Bean
   		public MyService myService() {
   			return new MyService();
   		}
   	}
   }
   
Implementing KafkaListenerConfigurer also allows for fine-grained control over endpoints registration via the KafkaListenerEndpointRegistrar. For example, the following configures an extra endpoint:
   {
   	@code
   	@Configuration
   	@EnableKafka
   	public class AppConfig implements KafkaListenerConfigurer {
   		@Override
   		public void configureKafkaListeners(KafkaListenerEndpointRegistrar registrar) {
   			SimpleKafkaListenerEndpoint myEndpoint = new SimpleKafkaListenerEndpoint();
   			// ... configure the endpoint
   			registrar.registerEndpoint(endpoint, anotherKafkaListenerContainerFactory());
   		}
  
   		@Bean
   		public MyService myService() {
   			return new MyService();
   		}
  
   		@Bean
   		public KafkaListenerContainerFactory<?, ?> anotherKafkaListenerContainerFactory() {
   			// ...
   		}
  
   		// Kafka infrastructure setup
   	}
   }
   
Note that all beans implementing KafkaListenerConfigurer will be detected and invoked in a similar fashion. The example above can be translated in a regular bean definition registered in the context in case you use the XML configuration.
See Also:
KafkaListener, KafkaListenerAnnotationBeanPostProcessor, org.springframework.kafka.config.KafkaListenerEndpointRegistrar, org.springframework.kafka.config.KafkaListenerEndpointRegistry
  spring-kafka-dist.spring-kafka.main



# flush


If you wish to block the sending thread, to await the result, you can invoke the future’s get() method. You may wish to invoke flush() before waiting or, for convenience, the template has a constructor with an autoFlush parameter which will cause the template to flush() on each send. Note, however that flushing will likely significantly reduce performance.

## Non Blocking (Async).
```java
public void sendToKafka(final MyOutputData data) {
final ProducerRecord<String, String> record = createRecord(data);
ListenableFuture<SendResult<Integer, String>> future = template.send(record); future.addCallback(new ListenableFutureCallback<SendResult<Integer, String>>() {
@Override
public void onSuccess(SendResult<Integer, String> result) { handleSuccess(data);
}
@Override
public void onFailure(Throwable ex) { handleFailure(data, record, ex);
}
}); }
```

## Blocking (Sync).
```java
public void sendToKafka(final MyOutputData data) {
final ProducerRecord<String, String> record = createRecord(data);
try {
template.send(record).get(10, TimeUnit.SECONDS); handleSuccess(data);
}
catch (ExecutionException e) {
        handleFailure(data, record, e.getCause());
    }
catch (TimeoutException | InterruptedException e) { handleFailure(data, record, e);
} }
```



## KafkaTransactionManager
The `KafkaTransactionManager` is an implementation of Spring Framework’s `PlatformTransactionManager`;


