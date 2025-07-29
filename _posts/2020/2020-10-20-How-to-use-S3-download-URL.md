---
title: How to process data from S3 download URL
date: 2020-10-20
tags:
 - AWS
 - S3
 - NIO

layout: posts
---

# S3 download URL
As you know, AWS S3 object can be downloaded/processed by S3 download URL. 
I'm showing you two examples on how to process S3 Object by NIO from Java.

# How to use S3 download URL

Below are Java samples to download S3 Object. 
## Save as a local file
The frist one is save S3 file to a file in local disk
 
```java
  private void readS3FileToFile(String url, Path filePath) throws IOException {
        logger.info("Going to save file to be downloaded from S3");
        try (ReadableByteChannel srcChannel = Channels.newChannel(new URL(url).openStream());
             FileOutputStream outputStream = new FileOutputStream(filePath.toFile());
             FileChannel fileChannel = outputStream.getChannel()) {
            fileChannel.transferFrom(srcChannel, 0, Integer.MAX_VALUE);
            logger.info(" File downloaded and saved to: " + filePath.toString());
        }
    }
```

## Output file content to String

```java
    private void readS3FileToString(String url) throws IOException {
        logger.info("Going to read file content directly from S3");
        try (ReadableByteChannel channel = Channels.newChannel(new URL(url).openStream());
             ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
             WritableByteChannel writeChannel = Channels.newChannel(outputStream)) {


            ByteBuffer buffer = ByteBuffer.allocate(1_024);
            boolean readon = true;
            while (readon) {
                int len = channel.read(buffer);
                if (len <= 0) {
                    readon = false;
                }
                buffer.flip();
                writeChannel.write(buffer);
                buffer.clear();
            }
            String fileContent = outputStream.toString();
            logger.info(" File content is : " + fileContent);
        }
    }
```
--End--
