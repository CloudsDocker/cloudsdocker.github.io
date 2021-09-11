---
title: QuickFixJ 
layout: posts
---

# Settings

A settings file is set up with two types of heading, a [DEFAULT] and a [SESSION] heading. [SESSION] tells QuickFIX/J that a new Session is being defined. [DEFAULT] is a place that you can define settings which will be inherited by sessions that do not explicitly define them. If you do not provide a setting that QuickFIX/J needs, it will throw a ConfigError telling you what setting is missing or improperly formatted.

# SSL cipher

An SSL cipher specification in cipher-spec is composed of 4 major attributes plus a few extra minor ones.

Key Exchange Algorithm:
RSA or Diffie-Hellman variants.

Authentication Algorithm:
RSA, Diffie-Hellman, DSS or none.

Cipher/Encryption Algorithm:
DES, Triple-DES, RC4, RC2, IDEA or none.

MAC Digest Algorithm:
MD5, SHA or SHA1.

## InOut exchange
Although the `FIX protocol is event-driven and asynchronous`, there are specific pairs of messages
that represent a request-reply message exchange. To use an InOut exchange pattern, there should
be a single request message and single reply message to the request. Examples include an 
OrderStatusRequest message and UserRequest.

#FIX Sequence Number Management
If an application exception is thrown during synchronous exchange processing, this will cause QuickFIX/J to not increment incoming FIX message sequence numbers and will cause a resend of the counterparty message. This FIX protocol behavior is primarily intended to handle transport errors rather than application errors. There are risks associated with using this mechanism to handle application errors. The primary risk is that the message will repeatedly cause application errors each time it is re-received. A better solution is to persist the incoming message (database, JMS queue) immediately before processing it. This also allows the application to process messages asynchronously without losing messages when errors occur.

Although it is possible to send messages to a FIX session before it is logged on (the messages will be sent at logon time), it is usually a better practice to wait until the session is logged on. This eliminates the required sequence number resynchronization steps at logon. Waiting for session logon can be done by setting up a route that processes the SessionLogon event category and signals the application to start sending messages.


# Source code
## QuickFixJComponent.class

if (configuration != null) {
                        settings = configuration.createSessionSettings();
                    } else {
                        settings = QuickfixjEngine.loadSettings(remaining);
                    }

## MessageStore
This interface Used by a Session to store and retrieve messages for resend purposes.

- boolean set(int sequence, String message) throws IOException;
- void get(int startSequence, int endSequence, Collection<String> messages) throws IOException;

Implementations such as MemoryStore.java, it use one HashMap<Integer, String> to keep messages (string)

## Parse body
private void parseBody(DataDictionary dd, boolean doValidation) throws InvalidMessage {
        for(StringField field = this.extractField(dd, this); field != null; field = this.extractField(dd, this)) {
            if (isTrailerField(field.getField())) {
                this.pushBack(field);
                return;
            }


## validate check sum
in message.class

private void validateCheckSum(String messageData) throws InvalidMessage {
        try {
            int checksum = this.trailer.getInt(10);
            if (checksum != MessageUtils.checksum(messageData)) {
                throw new InvalidMessage("Expected CheckSum=" + MessageUtils.checksum(messageData) + ", Received CheckSum=" + checksum + " in " + messageData);
            }
}

the first checksum is 131

in MessageUtils.checksum
public static int checksum

int end = isEntireMessage ? data.lastIndexOf("\u000110=") : -1;
            int len = end > -1 ? end + 1 : data.length();

            for(int i = 0; i < len; ++i) {
                sum += data.charAt(i);
            }

            return sum & 255;
the checksum from above messageUtil is 87
?? how to get and set this.trailer.10=131 ?
