Sample me build a micro service payment system with spring cloud

Sure! Here's an example of building a microservice payment system using Spring Cloud:

Create a new Spring Boot project for the payment service using your preferred IDE or the Spring Initializr.
Add the Eureka client and Ribbon dependencies to your project's build file. You can do this by adding the following lines to your pom.xml file if you are using Maven:
php
Copy code
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
</dependency>

<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-netflix-ribbon</artifactId>
</dependency>
Enable Eureka client-side service discovery in your application by adding @EnableDiscoveryClient annotation to your application class.
less
Copy code
@SpringBootApplication
@EnableDiscoveryClient
public class PaymentServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(PaymentServiceApplication.class, args);
    }
}
Create a REST endpoint in your payment service to handle payment requests. For example:
less
Copy code
@RestController
public class PaymentController {

    @GetMapping("/payment/{orderId}")
    public ResponseEntity<String> processPayment(@PathVariable String orderId) {
        // ... process payment ...
        return ResponseEntity.ok("Payment processed for order " + orderId);
    }
}
Configure your payment service to use Ribbon for load balancing by adding the following properties to your application.properties or application.yml file:
bash
Copy code
payment.service.name=payment-service

ribbon.eureka.enabled=true
ribbon.OkToRetryOnAllOperations=true
ribbon.MaxAutoRetriesNextServer=3
ribbon.MaxAutoRetries=1

payment.service.ribbon.listOfServers=http://localhost:8081,http://localhost:8082
In the above example, payment-service is the name of the service that the payment service will be calling.

Create a new Spring Boot project for the order service and repeat steps 2-5, replacing the payment with order wherever appropriate.
Use the DiscoveryClient to look up the instances of the service you want to call and use Ribbon for load balancing between them. For example:
typescript
Copy code
@RestController
public class OrderController {

    @Autowired
    private DiscoveryClient discoveryClient;

    @Autowired
    private RestTemplate restTemplate;

    @GetMapping("/order/{orderId}")
    public ResponseEntity<String> processOrder(@PathVariable String orderId) {
        List<ServiceInstance> instances = discoveryClient.getInstances("payment-service");
        String paymentServiceUri = instances.get(0).getUri().toString();
        String paymentUrl = paymentServiceUri + "/payment/" + orderId;
        ResponseEntity<String> response = restTemplate.getForEntity(paymentUrl, String.class);
        return ResponseEntity.ok("Order processed with payment: " + response.getBody());
    }
}
In the above example, we're using the DiscoveryClient to look up the instances of the payment-service and using Ribbon for load balancing between them. We then call the payment service's processPayment() endpoint and return the result.

Overall, using Spring Cloud to build microservices-based architectures can greatly simplify the configuration and management of distributed systems. It allows services to dynamically discover and communicate with each other, improving the overall scalability, resilience, and fault tolerance of the system.
