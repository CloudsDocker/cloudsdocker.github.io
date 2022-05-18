---
header:
    image: /assets/images/hd_FirstCliff.jpg
title: How to copy files from resources folder in jar and save to a file
date: 2021-11-15
tags:
 - jar
 - Java
 - IntelliJ
permalink: /blogs/tech/en/save_resources_to_files
layout: posts
---


# Why to extract resources from jar to local disk



# How to save resource to local  disk

Firslty let's define a class to represen the file extracted from resoruce folder

```java
import lombok.Builder;
import lombok.Data;

import java.util.Date;

@Data
@Builder
class FileInfo {
    String fileInfo;
    String fileSize;
    Date lastModified;
}

```

Then create a helper class to extract file out of resource folder and save to local disk. 
> The dirty job done by ResourceLoader which is one out-of-box helper class from Springframwork

```java

import ch.qos.logback.core.util.FileUtil;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.FileUtils;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Component;
import org.springframework.util.FileCopyUtils;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Date;

@Component
@RequiredArgsConstructor
@Slf4j
public class KeyTabFilesHelper {


    /**
     * This final ResourceLoader + @RequiredArgsConstructor will make this loader automatically wired from Spring
     */
    private final ResourceLoader resourceLoader;


    /**
     * Extract file content from jar file's Resource folder, then save it to local disk
     * @param resourceFolder relative folder under project "resource" folder
     * @param resourceName resource name
     * @param destPath path of local disk the resource to be saved
     * @return A data class provide a summary of the file saved
     */
    @SneakyThrows
    public FileInfo saveAsFile(String resourceFolder, String resourceName, String destPath) {
        final val resource = resourceLoader.getResource("classpath:" + resourceFolder + File.separator + resourceName);
        final val path = Paths.get(destPath, resourceName);


        if (!Files.exists(path)) {
            log.info("File NOT exist, create it and it's missing parent folder :{}", path);
            File file = new File(path.toString());
            FileUtil.createMissingParentDirectories(file);
        }

        FileCopyUtils.copy(resource.getInputStream(), new FileOutputStream(path.toFile()));

        final val fileInfo = FileInfo.builder()
                .fileInfo(path.toFile().toString())
                .fileSize(FileUtils.byteCountToDisplaySize(Files.size(path)))
                .lastModified(new Date(path.toFile().lastModified()))
                .build();

        log.info("saved file to {}, file is:{}", path, fileInfo);
        return fileInfo;
    }

}
```


# Normal approach to debug maven

Normaly if you want to debug a Java application, you can use following procedures
- Running application with mvnDebug, such as `mvnDebug spring-boot:run`
- This will open a port such as `5005`
- Then open IntelliJ, create a `remote JVM debug` , attach it to port 5005 for debug

![](/assets/images/Run_Debug_Configurations.png)

However, sometimes you'll find **your breakpoints nevet got hit**. 

# Better/Alternative way to solve this issue.

1. Open a new terminal **within Intellij** (rather than external command line window).

2. Navigate to your *project folder* where pom.xml saved

3. Run following command
```bash
mvn spring-boot:run  -D"spring-boot.run.jvmArguments"="-Dimport.dataset.list=importpb -Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=y,address=5005"
```
After a while, you'll see following message indicate progress is listenring at designed port

```bash
[INFO] Attaching agents: []
Listening for transport dt_socket at address: 5005
```

4. Then start a new JVM debug window on port 5005, as below screenshot:

![](/assets/images/Run_Debug_Configurations.png)

5. Start debug with aforesaid debug configuration
![](/assets/images/debugIconIntelliJ.png)

6. Then you'll see breakpoint you set will be hit. As per below screenshot
![](/assets/images/BreakpointSpringBootApplication.png)


--End--
