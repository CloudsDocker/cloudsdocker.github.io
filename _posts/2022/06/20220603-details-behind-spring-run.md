---
title: Magic after maven target spring-boot-run
---
```
mvn spring-boot:run
```

The Spring Boot Maven plugin includes a run goal which can be used to quickly compile and run your application. Applications run in an exploded form just like in your IDE.



定位到 spring-boot-maven-plugin 项目里的RunMojo.java，就是mvn spring-boot:run 这个指令所运行的java代码。关键方法有两个，一个是 runWithForkedJvm，一个是runWithMavenJvm，如果pom.xml是如上述配置，则运行的是 runWithForkedJvm，如果pom.xml里的配置如下，则运行runWithMavenJvm:







run goal
```

<plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <mainClass>${start-class}</mainClass>
                    <classifier>deployable</classifier>
                </configuration>
                <executions>
                    <execution>
                        <id>default-cli</id>
                        <goals>
                            <goal>run</goal>
                        </goals>
                        <phase>none</phase>
                        <configuration>
                            <fork>true</fork>
                            <jvmArguments>${jvm.args} -Ddns.server=127.0.0.1 -Dspring.profiles.active=local</jvmArguments>
                            <folders>
                                <folder>${basedir}/src/test/resources</folder>
                            </folders>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
```

to debug maven plugin, replace mvn  with mvnDebug , then check following lines:

[INFO] Attaching agents: []
Listening for transport dt_socket at address: 5050
