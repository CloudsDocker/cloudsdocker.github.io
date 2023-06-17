---
title: Spring Cloud Master Piece 5
header:
image: /assets/images/yarn_npm_install.jpg
date: 2023-03-19
tags:
- JFR
- Java
- PerformanceTuning

permalink: /blogs/tech/en/spring_cloud_master_piece_5
layout: single
category: tech
---


How to add security among micro service  in spring boot

In a Spring Boot microservice architecture, you can add security using Spring Security and JSON Web Tokens (JWT) to secure communication between microservices. Here's how you can do it:

Set Up a Security Service
First, set up a separate security service to handle authentication and authorization. This service should be responsible for generating and validating JWT tokens.
Add Spring Security Dependencies
Next, add the following Spring Security dependencies to your microservices' pom.xml files:
xml
Copy code
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-security</artifactId>
</dependency>

<dependency>
  <groupId>io.jsonwebtoken</groupId>
  <artifactId>jjwt</artifactId>
  <version>0.9.1</version>
</dependency>
Configure Spring Security
Configure Spring Security in each of your microservices' application.yml files. Here's an example:
yaml
Copy code
spring:
  security:
    user:
      name: user
      password: password
  jwt:
    secret: your_secret_key
This configuration sets up a default user for development purposes and defines a secret key for generating and validating JWT tokens.

Implement a Security Filter
Create a security filter in each of your microservices to intercept incoming requests and validate JWT tokens. Here's an example:
java
Copy code
public class JwtTokenAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider jwtTokenProvider;

    public JwtTokenAuthenticationFilter(JwtTokenProvider jwtTokenProvider) {
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        String token = jwtTokenProvider.resolveToken(request);
        try {
            if (token != null && jwtTokenProvider.validateToken(token)) {
                Authentication auth = jwtTokenProvider.getAuthentication(token);
                SecurityContextHolder.getContext().setAuthentication(auth);
            }
        } catch (JwtException e) {
            SecurityContextHolder.clearContext();
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Invalid JWT token");
            return;
        }

        filterChain.doFilter(request, response);
    }
}
This filter intercepts incoming requests and validates the JWT token. If the token is valid, it sets the authentication context using the SecurityContextHolder. If the token is invalid, it returns an error response.

Configure the Security Filter
Configure the security filter in each of your microservices' WebSecurityConfigurerAdapter classes. Here's an example:
java
Copy code
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    private final JwtTokenProvider jwtTokenProvider;

    public SecurityConfig(JwtTokenProvider jwtTokenProvider) {
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.csrf().disable()
                .authorizeRequests()
                .antMatchers("/api/**").authenticated()
                .and()
                .addFilterBefore(new JwtTokenAuthenticationFilter(jwtTokenProvider), UsernamePasswordAuthenticationFilter.class);
    }
}
This configuration disables CSRF protection, authorizes requests to the /api endpoint, and adds the security filter to the filter chain.

With these changes, your microservices are now secured using Spring Security and JWT tokens.
