---
layout: posts
title: SSH and Cryptography
tags: 
- SSH
- Cryptography
---

# SFTP versus FTPS
- SS: Secure Shell
- An increasing number of our customers are looking to move away from standard FTP for transferring data, so we are often asked which secure FTP protocol we recommend. In the next few paragraphs, we will explain what options are available and their main differences.
- The two mainstream protocols available for Secure FTP transfers are named SFTP (FTP over SSH) and FTPS (FTP over SSL). Both SFTP and FTPS offer a high level of protection since they implement strong algorithms such as AES and Triple DES to encrypt any data transferred. Both options also support a wide variety of functionality with a broad command set for transferring and working with files. So the most notable differences between SFTP and FTPS is how connections are authenticated and managed.

## Authentication: SFTP vs. FTPS
- With SFTP (FTP over SSH), a connection can be authenticated using a couple different techniques.  For basic authentication, you (or your trading partner) may just require a user id and password to connect to the SFTP server. Its important to note that any user ids and passwords supplied over the SFTP connection will be encrypted, which is a big advantage over standard FTP.
- SSH keys can also be used to authenticate SFTP connections in addition to, or instead of, passwords. With key-based authentication, you will first need to generate a SSH private key and public key beforehand. If you need to connect to a trading partner's SFTP server, you would send your SSH public key to them, which they will load onto their server and associate with your account. When you connect to their SFTP server, your client software will transmit your public key to the server for authentication. If the keys match, along with any user/password supplied, then the authentication will succeed.
- With FTPS (FTP over SSL), a connection is authenticated using a user id, password and certificate(s).  Like SFTP, the users and passwords for FTPS connections will also be encrypted. When connecting to a trading partner's FTPS server, your FTPS client will first check if the server's certificate is trusted. The certificate is considered trusted if either the certificate was signed off by a known certificate authority (CA), like Verisign, or if the certificate was self-signed (by your partner) and you have a copy of their public certificate in your trusted key store.
- Your partner may also require that you supply a certificate when you connect to them.  Your certificate may be signed off by a 3rd party CA or your partner may allow you to just self-sign your certificate, as long as you send them the public portion of your certificate beforehand (which they will load in their trusted key store).

## Implementation: SFTP vs. FTPS
- In regards to how easy each of the secure FTP protocols are to implement, SFTP is the clear winner since it is very firewall friendly. SFTP only needs a single port number (default of 22) to be opened through the firewall.  This port will be used for all SFTP communications, including the initial authentication, any commands issued, as well as any data transferred.
- On the other hand, FTPS can be very difficult to patch through a tightly secured firewall since FTPS uses multiple port numbers. The initial port number (default of 21) is used for authentication and passing any commands.  However, every time a file transfer request (get, put) or directory listing request is made, another port number needs to be opened.  You and your trading partners will therefore have to open a range of ports in your firewalls to allow for FTPS connections, which can be a security risk for your network.

In summary, SFTP and FTPS are both very secure with strong authentication options.  However since SFTP is much easier to port through firewalls, and we are seeing an increasing percentage of trading partners adopting SFTP, we believe SFTP is the clear winner for your secure FTP needs.

# SSH
- There are several ways to use SSH; one is to use automatically generated public-private key pairs to simply encrypt a network connection, and then use password authentication to log on.
- Another is to use a manually generated public-private key pair to perform the authentication, allowing users or programs to log in without having to specify a password. In this scenario, anyone can produce a matching pair of different keys (public and private). The public key is placed on all computers that must allow access to the owner of the matching private key (the owner keeps the private key secret). While authentication is based on the private key, the key itself is never transferred through the network during authentication. SSH only verifies whether the same person offering the public key also owns the matching private key. In all versions of SSH it is important to verify unknown public keys, i.e. associate the public keys with identities, before accepting them as valid. Accepting an attacker's public key without validation will authorize an unauthorized attacker as a valid user.
- SSH is important in cloud computing to solve connectivity problems, avoiding the security issues of exposing a cloud-based virtual machine directly on the Internet. An SSH tunnel can provide a secure path over the Internet, through a firewall to a virtual machine.
- The standard TCP port 22 has been assigned for contacting SSH servers.

## Key management
- On Unix-like systems, the list of authorized public keys is typically stored in the home directory of the user that is allowed to log in remotely, in the file ~/.ssh/authorized_keys.

### WinFTP
- cryptographic protocol is SSH-2
- SSH implementation is OpenSSH_5.3
- Server fingerprint: File transfer protocol = SFTP-3
Cryptographic protocol = SSH-2
SSH implementation = OpenSSH_5.3
Encryption algorithm = aes
Compression = No
------------------------------------------------------------
Server host key fingerprint
ssh-rsa 2048 86:54:d9:09:25:c0:9b:f8:17:8c:c0:52:13:0c:9c:cc
------------------------------------------------------------

# ssh-keygen
- ssh-keygen is a standard component of the Secure Shell (SSH) protocol suite found on Unix and Unix-like computer systems used to establish secure shell sessions between remote computers over insecure networks, through the use of various cryptographic techniques. The ssh-keygen utility is used to generate, manage, and convert authentication keys.
- ssh-keygen is able to generate a key using one of three different digital signature algorithms.
- With the help of the ssh-keygen tool, a user can create passphrase keys for any of these key types (to provide for unattended operation, the passphrase can be left empty, at increased risk).

## algorithm
- SSH protocol version 1 (now deprecated) only the RSA algorithm was supported.
- The SSH protocol version 2 additionally introduced support for the DSA algorithm.
- Subsequently, OpenSSH added support for a third digital signature algorithm, ECDSA 


# DSA
- The Digital Signature Algorithm (DSA) is a Federal Information Processing Standard for digital signatures. It was proposed by the National Institute of Standards and Technology (NIST) in August 1991 for use in their Digital Signature Standard (DSS) and adopted as FIPS 186 in 1993

# Hash 
In cryptography applications, we often need a so-called secure hash function. Secure hash functions are generaelly a subset of hash functions that fulfil at least two extra criteria:

- it must be computationally impossible to reverse the mapping, that is, go from a hash code to a message or piece of data that would have generated that hash code;
- it must be infeasible for a collision to occur: that is, for two messages to be found that have the same hash code.

In order to fulfil these criteria (or at least, as a by-product of needing to fulfil these criteria), secure hash functions generally have these characteristics:

they are slower to compute than the hash codes typically used to key hash maps;
they are wider (i.e. have more bits) than weak hash codes.

Secure hash codes are typically 128 bits wide at the very least; compare that, for example, to the 32-bit codes returned by Java hashCode() method, or the 64-bit hash codes recommended for key-less hash maps in Numerical Recipes.

Applications of secure hash functions
Secure hash functions actually have various applications. A very common case is verifying the integrity of data. When we send some data, we append a hash of that data; on the receiving end, we re-hash the received data and check that the computed hash equals that sent; if any of the data has changed then (with overwhelming probability), the computed hash value will no longer match the original. Another case is where we need to authenticate some data, i.e. produce a kind of integrity check that only a party with a given private key could produce. (In this case, the general solution is to combine a hash code with encryption.)

In other cases, a secure hash function is useful to represent a particular item of data. For example, for the purpose of checking passwords, we need only store a hash of that password. When somebody enters their password, if the computed hash of what they entered matches the hash stored in the password file/database, we assume they knew the password.

This scheme, sometimes called compare by hash (CBH) can be used to search for duplicates of data on a hard drive or for synching data between multiple machines. Similarly, another example are the databases that various law enforcement agencies keep of known "disapproved" files that they want to search peoples hard drives for. In these applications, keeping a database of the actual file contents, and/or transmitting and comparing those entire contents, would be impractical. Instead, only hashes are stored and compared.

More broadly, secure hash functions are useful in a variety of cases where we need a trapdoor function (i.e. one that cannot feasibly be reversed), especially where we need one with a limited or fixed-size result.

As mentioned, secure hashes are sometimes called message digests. And in fact, the main class for computing them in Java is java.security.MessageDigest. We get an instance of MessageDigest, feed it an array (or several arrays) of bytes, then call its digest() method to get the resulting hash:

```java
byte[] data = ....

MessageDigest md = MessageDigest.getInstance("SHA-1");
md.update(data);
byte[] hash = md.digest();
```

## MD5
MD5 is a later hash function developed by Ron Rivest. It is one of the most common hash algorithms in use today. Like MD2, it is a 128-bit hash function but, unlike its predecessor, it is one of the fastest "secure" hash functions in common use, and the fastest provided in Java 6.

Unfortunately, it is now considered insecure. Aside from the relatively small hash size, there are well-published methods to find collisions analytically in a trivial amount of time. For example, Vlastimil Klima has published a C program to find MD5 collisions in around 30 seconds on an average PC. If you need security, dont use MD5!

Although insecure, MD5 still makes a good general strong hash function due to its speed. In non-security applications such as finding duplicate files on a hard disk (where you are not trying to protect against the threat model of somebody deliberately fooling your system), MD5 makes a good choice.

## SHA algorithms
SHA (Secure Hash Algorithm) refers collectively to various hash functions developed by the US National Security Agency (NSA). The various algorithms are based on differing hash sizes and (in principle) offer corresponding levels of security:

# PBE  password-based encryption

The technique of generating a secret key from a user-generated passphrase is usually called password-based encryption (PBE). As you might imagine, it is fraught with difficulty. In particular:

- the user is requirement and the security requirement usually conflict: the user requires an easy-to-remember passphrase, or at least one that is made of recognisable characters and short enough to write down; yet for secure encryption by today is standards, we require at least 128 strongly random bits (and ideally more);
- password-based encryption is typically used in applications where an attacker can repeatedly try to guess the password undetected and beyond the control of the genuine sender/recipient (if the password is being used to log into our server, we can detect that so many invalid attempts were made and in the worst case shut down our server to prevent further attempts; but if an eavesdropper takes a copy of the encrypted ZIP file we e-mailed, we will never know that they are sitting there with a 100,000-processor botnet trying to brute-force the password, and they can essentially sit doing it for as long as they like).
The typical result is fairly dire: most password-protected data is encrypted with weak encryption keys, and an attacker can spend all the processor time they like trying to guess that weak key with complete impunity.

## How to use PBE
There are two fundamental problems: 
(a) user-memorable passwords typically dont contain as much randomness as we need for a secure key; 
(b) in a typical application, an attacker gets as many tries as they like at the password. An additional problem is that if, say, the password abc123 always generated the same key in our application, then an attacker could calculate the key from this password once and then quickly decrypt any data protected with this password.

Two common techniques are used in password-based encryption to try to alleviate these problems:

- a deliberately slow method is used to derive the encryption key from the password, reducing the number of guesses that an attacker can make in a given time frame;
- some random bytes, called a salt, are appended to the password before it is used to calculate the key.


# Cryptographic hash function
- A cryptographic hash function is a special class of hash function that has certain properties which make it suitable for use in cryptography. **It is a mathematical algorithm that maps data of arbitrary size to a bit string of a fixed size** (a hash function) which is designed to also be **a one-way function**, that is, a function which is infeasible to invert. The only way to recreate the input data from an ideal cryptographic hash function is output is **to attempt a brute-force search** of possible inputs to see if they produce a match. 
-  Bruce Schneier has called one-way hash functions the workhorses of modern cryptography.[1] The input data is often called the message, and the output (the hash value or hash) is often called the message digest or simply the `digest`.
- in information-security contexts, cryptographic hash values are sometimes called (digital) fingerprints, checksums, or just hash values, even though all these terms stand for more general functions with rather different properties and purposes.
- Another finalist from the NIST hash function competition, BLAKE, was optimized to produce BLAKE2 which is notable for being faster than SHA-3, SHA-2, SHA-1, or MD5, and is used in numerous applications and libraries.

## The ideal cryptographic hash function has five main properties:
- it is deterministic so the same message always results in the same hash
- it is quick to compute the hash value for any given message
- it is infeasible to generate a message from its hash value except by trying all possible messages
- a small change to a message should change the hash value so extensively that the new hash value appears uncorrelated with the old hash value
- it is infeasible to find two different messages with the same hash value

### Illustration
- An illustration of the potential use of a cryptographic hash is as follows: Alice poses a tough math problem to Bob and claims she has solved it. Bob would like to try it himself, but would yet like to be sure that Alice is not bluffing. Therefore, Alice writes down her solution, computes its hash and tells Bob the hash value (whilst keeping the solution secret). Then, when Bob comes up with the solution himself a few days later, Alice can prove that she had the solution earlier by revealing it and having Bob hash it and check that it matches the hash value given to him before. (This is an example of a simple commitment scheme; in actual practice, Alice and Bob will often be computer programs, and the secret would be something less easily spoofed than a claimed puzzle solution).

### Applications
#### Verifying the integrity of files or messages
- An important application of secure hashes is verification of message integrity. Determining whether any changes have been made to a message (or a file), for example, can be accomplished by comparing message digests calculated before, and after, transmission (or any other event).
- For this reason, most digital signature algorithms only confirm the authenticity of a hashed digest of the message to be "signed". Verifying the authenticity of a hashed digest of the message is considered proof that the message itself is authentic.
- **MD5, SHA1, or SHA2 hashes** are sometimes posted along with files on websites or forums to allow verification of integrity.[6] This practice establishes a chain of trust so long as the hashes are posted on a site authenticated by HTTPS.

#### Password verification
- Storing all user passwords as cleartext can result in a massive security breach if the password file is compromised. One way to reduce this danger is to only store the hash digest of each password. To authenticate a user, the password presented by the user is hashed and compared with the stored hash. 
- The password is often concatenated with a random, non-secret salt value before the hash function is applied. The salt is stored with the password hash. Because users have different salts, it is not feasible to store tables of precomputed hash values for common passwords. 

## MD5
- The MD5 algorithm is a widely used hash function producing a 128-bit hash value. Although MD5 was initially designed to be used as a cryptographic hash function, it has been found to suffer from extensive vulnerabilities. It can still be used as a checksum to verify data integrity, but only against unintentional corruption.
- Like most hash functions, **MD5 is neither encryption nor encoding**. It **can be reversed by brute-force attack** and suffers from extensive vulnerabilities as detailed in the security section below.
- MD5 was designed by Ronald Rivest in 1991 to replace an earlier hash function MD4.
- The MD5 hash function receives its acronym MD from its structure using Merkle–Damg?rd construction.

### Collision resistance
- Collision resistance is a property of cryptographic hash functions: a hash function H is collision resistant if it is hard to find two inputs that hash to the same output; that is, two inputs a and b such that H(a) = H(b), and a ≠ b
- Collision resistance does not mean that no collisions exist; simply that they are hard to find.
- Cryptographic hash functions are usually designed to be collision resistant. But many hash functions that were once thought to be collision resistant were later broken. MD5 and SHA-1 in particular both have published techniques more efficient than brute force for finding collisions.

#### Rationale
Collision resistance is desirable for several reasons.
- In some digital signature systems, a party attests to a document by publishing a public key signature on a hash of the document. If it is possible to produce two documents with the same hash, an attacker could get a party to attest to one, and then claim that the party had attested to the other.
- In some proof-of-work systems (e.g. bitcoin mining), users provide hash collisions as proof that they have performed a certain amount of computation to find them. If there is an easier way to find collisions than brute force, users can cheat the system.
- In some distributed content systems, parties compare cryptographic hashes of files in order to make sure they have the same version. An attacker who could produce two files with the same hash could trick users into believing they had the same version of a file when they in fact did not.

#### Algorithm
- The Merkle–Damg?rd hash function first applies an MD-compliant padding function to create an input whose size is a multiple of a fixed number (e.g. 512 or 1024) — this is because compression functions cannot handle inputs of arbitrary size. The hash function then breaks the result into blocks of fixed size, and processes them one at a time with the compression function, each time combining a block of the input with the output of the previous round.[1]:146 In order to make the construction secure, Merkle and Damg?rd proposed that messages be padded with a padding that encodes the length of the original message. This is called **length padding** or Merkle–Damg?rd strengthening.
- In the diagram, the one-way compression function is denoted by f, and transforms two fixed length inputs to an output of the same size as one of the inputs. The algorithm starts with an initial value, the initialization vector (IV). The IV is a fixed value (algorithm or implementation specific). For each message block, the compression (or compacting) function f takes the result so far, combines it with the message block, and produces an intermediate result. The last block is padded with zeros as needed and bits representing the length of the entire message are appended. (See below for a detailed length padding example.)
- To harden the hash further the last result is then sometimes fed through a finalisation function. The finalisation function can have several purposes such as compressing a bigger internal state (the last result) into a smaller output hash size or to guarantee a better mixing and avalanche effect on the bits in the hash sum. The finalisation function is often built by using the compression function[citation needed] (Note that in some documents instead the act of length padding is called "finalisation").

### Merkle–Damg?rd construction
- In cryptography, the Merkle–Damg?rd construction or **Merkle–Damg?rd hash function** is a method of building collision-resistant cryptographic hash functions from collision-resistant one-way compression functions.[1]:145 This construction was used in the design of many popular hash algorithms such as MD5, SHA1 and SHA2.
- The Merkle–Damg?rd construction was described in Ralph Merkles Ph.D. thesis in 1979.[2] Ralph Merkle and Ivan Damg?rd independently proved that the structure is sound: that is, if an appropriate padding scheme is used and the compression function is collision-resistant, then the hash function will also be collision resistant.

## SHA 
- In cryptography, SHA-1 (Secure Hash Algorithm 1) is a cryptographic hash function designed by the United States National Security Agency and is a U.S. Federal Information Processing Standard published by the United States NIST.[2] SHA-1 produces a 160-bit (20-byte) hash value known as a message digest. A SHA-1 hash value is typically rendered as a hexadecimal number, 40 digits long.

### Applications
- SHA-1 forms part of several widely used security applications and protocols, including TLS and SSL, PGP, SSH, S/MIME, and IPsec. Those applications can also use MD5; **both MD5 and SHA-1 are descended from MD4**. **SHA-1 hashing is also used in distributed revision control systems like Git**, Mercurial, and Monotone to identify revisions, and to detect data corruption or tampering. The algorithm has also been used on Nintendos Wii gaming console for signature verification when booting, but a significant flaw in the first implementations of the firmware allowed for an attacker to bypass the systems security scheme.
- SHA-1 and SHA-2 are the secure hash algorithms required by law for use in certain U.S. Government applications, including use within other cryptographic algorithms and protocols, for the protection of sensitive unclassified information.
- A prime motivation for the publication of the Secure Hash Algorithm was the Digital Signature Standard, in which it is incorporated.
- Revision control systems such as Git and Mercurial use SHA-1 not for security but for ensuring that the data has not changed due to accidental corruption.

## Salt (cryptography)
- In cryptography, a salt is random data that is used as an additional input to a one-way function that "hashes" a password or passphrase. Salts are closely related to the concept of nonce. The primary function of salts is to defend against dictionary attacks or against its hashed equivalent, a pre-computed rainbow table attack.[1]
- Salts are used to safeguard passwords in storage. 
- The purpose of a hash and salt process in password security is not to prevent a password from being guessed, but to prevent a leaked password database from being used in further attacks.

The idea of salt is that when the user enters the password, we dont actually use their raw password to generate the key. We first append some random bytes to the password. A new, random salt is used for every file/piece of data being encrypted. The salt bytes are not secret: they are stored unencrypted along side the encrypted data. This means that the salt bytes would add no extra security if there was only once piece of data in the world encrypted with a given password. But they prevent dictionary attacks, whereby an attacker pre-computes the keys from some common passwords and then tries those keys on the encrypted data. Without salt bytes, the dictionary attack would be worthwhile attack because we use a deliberately slow function to derive a key from a password. With the salt bytes, the attacker is forced to run the slow key derivation function for each password they want to try on each piece of data.

To generate salt bytes in Java, we just need to make sure that we use a secure random number generator. Construct an instance of SecureRandom, create (say) a 20-byte array, and call nextBytes() on that array:
```java
Random r = new SecureRandom();
byte[] salt = new byte[20];
r.nextBytes(salt);
```

# Secure Random
The SecureRandom class, housed in the java.security package, provides a drop-in replacement to java.lang.Random. But unlike the latter, java.security.SecureRandom is designed to be cryptographically secure. 

SecureRandom is typically used in cases where:

random numbers are generated for security related purposes, such as generating an encryption key or session ID (see below);
or, more generally, high-quality randomness is important and it is worth consuming CPU (or where CPU consumption is not an issue) to generate those high-quality random numbers.

## Properties of SecureRandom
We said that SecureRandom is designed to be cryptographically secure. In practice, this means that the generator has the following properties:

- given only a number produced by the generator, it is (to all intents and purposes) impossible to predict previous and future numbers;
- the numbers produced contain no known biases;
- the generator has a large period (in Suns standard implementation, based on the 160-bit SHA1 hash function, the period is 2160);
- the generator can seed itself at any position within that period with equal probability (or at least, it comes so close to this goal, that we have no practical way of telling otherwise).

These properties are important in various security applications. The first is important, for eaxmple, if we use the generator to produce, say, a session ID on a web server: we donot want user n to predict user n+1 s session ID. Similarly, we donot want a user in an Internet cafe, based on the session ID or encryption key that they are given to access a web site, to be able to predict the value assigned to a previous user on that machine.

## The importance of producing all values with equal probability

For example, let s say that we want to pick a 128-bit AES encryption key. The idea of a strong encryption algorithm such as AES is that in order for an adversary to guess the key by "brute force" (which we assume is the only possible means), they would have to try every single possible key in turn until they hit on the right one. By law of averages, we would expect them to find it after half as many guesses as there are possible keys. A 128-bit key has 2128 possible values, so on average, they would have to try 2127 keys. In decimal 2127 is a 39-digit number. Or put another way, trying a million million keys per second, it would take 5x1015 millennia to try 2127 keys. Not even the British government wants to decrypt your party invitations that badly. So with current mainstream technology1, a 128-bit key is in principle sufficient for most applications.

But these metrics hold true only if our key selection algorithm— i.e. our random number generator— genuinely can pick any of the possible keys. For example, we certainly should not choose the key as follows:
```java
// This is WRONG!! Do not do this!
Random ranGen = new Random();
byte[] aesKey = new byte[16]; // 16 bytes = 128 bits
ranGen.nextBytes(aesKey);
```
The problem here is that the period of java.util.Random is only 248. Even though we are generating a 128-bit key, we will only ever pick from a subset of 248 of the possible keys. Or put another way: an attacker need only try on average 247 keys, and will find our key by trial and error in a couple of days if they try just a thousand million keys per second. And as if that wasnot bad enough, they probably donot even need to try anywhere near 247: for reasons discussed earlier, there is a good chance that an instance of java.util.Random created within a couple of minutes of bootup will actually be seeded from a about one thousandth of the 248 possible values. This time, HM Sniffing Service doesnot even need expensive hardware to find the secret location of your housewarming party: a trip to Staples will give them all the computing power they need.

So as you've probably guessed, our solution to the problem is to use SecureRandom instead:

import java.security.SecureRandom;
..
Random ranGen = new SecureRandom();
byte[] aesKey = new byte[16]; // 16 bytes = 128 bits
ranGen.nextBytes(aesKey);
Now, there's a good chance that any of the 2128 possible keys will be chosen.

Seeding of SecureRandom
In order to provide this property of choosing any seed with "equal" likelihood, (or at least, with no bias that is practically detectable), SecureRandom seeds itself from sources of entropy available from the local machine, such as timings of I/O events.




## 

## Rainbow table
- A rainbow table is a precomputed table for reversing cryptographic hash functions, **usually for cracking password hashes**. 
- Tables are **usually used in recovering a plaintext password up to a certain length consisting of a limited set of characters**. It is a practical example of a space/time trade-off, using less computer processing time and more storage than a brute-force attack which calculates a hash on every attempt, but more processing time and less storage than a simple lookup table with one entry per hash. 
- After gathering a password hash, using said hash as a password would fail since the authentication system would hash it a second time. In order to learn a users password, a password that produces the same hashed value must be found, usually through a brute-force or dictionary attack.
- Use of a **key derivation function that employs a salt** makes this attack infeasible.


## Passphrase
- A passphrase is a sequence of words or other text used to control access to a computer system, program or data. A passphrase is similar to a password in usage, but is generally longer for added security. Passphrases are often used to control both access to, and operation of, cryptographic programs and systems, especially those that derive an encryption key from a passphrase. The origin of the term is by analogy with password. The modern concept of passphrases is believed to have been invented by Sigmund N. Porter[1] in 1982.

### Compared to password
- Passphrases differ from passwords. A password is usually short—six to ten characters. Such passwords may be adequate for various applications (if frequently changed, if chosen using an appropriate policy, if not found in dictionaries, if sufficiently random, and/or if the system prevents online guessing, etc.)
- But passwords are typically not safe to use as keys for standalone security systems (e.g., encryption systems) that expose data to enable offline password guessing by an attacker.[citation needed] Passphrases are theoretically stronger, and so should make a better choice in these cases. First, they usually are (and always should be) much longer—20 to 30 characters or more is typical—making some kinds of brute force attacks entirely impractical. Second, if well chosen, they will not be found in any phrase or quote dictionary, so such dictionary attacks will be almost impossible. Third, they can be structured to be more easily memorable than passwords without being written down, reducing the risk of hardcopy theft.[citation needed] However, if a passphrase is not protected appropriately by the authenticator and the clear-text passphrase is revealed its use is no better than other passwords. For this reason it is recommended that passphrases not be reused across different or unique sites and services.

## Dictionary Attack
- In cryptanalysis and computer security, a dictionary attack is a technique for defeating a cipher or authentication mechanism by trying to determine its decryption key or passphrase by trying hundreds or sometimes millions of likely possibilities, such as words in a dictionary.
- A dictionary attack is based on trying all the strings in a pre-arranged listing, typically derived from a list of words such as in a dictionary (hence the phrase dictionary attack).
- **In contrast to a brute force attack**, where a large proportion of the **key space is searched systematically**, a **dictionary attack** tries **only those possibilities** which are deemed **most likely** to succeed. 
- Dictionary attacks often succeed because many people have a tendency to choose short passwords that are ordinary words or common passwords, or simple variants obtained, for example, by appending a digit or punctuation character. Dictionary attacks are relatively easy to defeat, e.g. by using a passphrase or otherwise choosing a password that is not a simple variant of a word found in any dictionary or listing of commonly used passwords.
- It is possible to achieve a time-space tradeoff by pre-computing a list of hashes of dictionary words, and storing these in a database using the hash as the key. This requires a considerable amount of preparation time, but allows the actual attack to be executed faster. 
- A more refined approach involves the use of rainbow tables, which reduce storage requirements at the cost of slightly longer lookup times. 
- **Pre-computed dictionary attacks, or "rainbow table attacks", can be thwarted by the use of salt**, a technique that forces the hash dictionary to be recomputed for each password sought, making precomputation infeasible provided the number of possible salt values is large enough.

# Avalanche effect
- In cryptography, the avalanche effect is the desirable property of cryptographic algorithms, typically block ciphers and cryptographic hash functions wherein if when an input is changed slightly (for example, flipping a single bit) the output changes significantly (e.g., half the output bits flip). In the case of high-quality block ciphers, such a small change in either the key or the plaintext should cause a drastic change in the ciphertext. The actual term was first used by Horst Feistel,[1] although the concept dates back to at least Shannon's diffusion.
-  The SHA-1 hash function exhibits good avalanche effect. When a single bit is changed the hash sum becomes completely different. If a block cipher or cryptographic **hash function does not exhibit the avalanche effect to a significant degree, then it has poor randomization**, and thus a cryptanalyst can make predictions about the input, being given only the output. This may be sufficient to partially or completely break the algorithm. Thus, the avalanche effect is a desirable condition from the point of view of the designer of the cryptographic algorithm or device.

# Public-key cryptography
- An unpredictable (typically large and random) number is used to begin generation of an acceptable pair of keys suitable for use by an asymmetric key algorithm.
- In an asymmetric key encryption scheme, anyone can encrypt messages using the public key, but only the holder of the paired private key can decrypt. Security depends on the secrecy of the private key.
-  In the Diffie–Hellman key exchange scheme, each party generates a public/private key pair and distributes the public key. After obtaining an authentic copy of each other's public keys, Alice and Bob can compute a shared secret offline. The shared secret can be used, for instance, as the key for a symmetric cipher.
- Public key cryptography, or asymmetric cryptography, is any cryptographic system that uses pairs of keys: public keys which may be disseminated widely, and private keys which are known only to the owner. This accomplishes two functions: **authentication**, which is when the public key is used to verify that a holder of the paired private key sent the message, and **encryption**, whereby only the holder of the paired private key can decrypt the message encrypted with the public key.
- In a public key encryption system, any person can encrypt a message using the public key of the receiver, but such a message can be decrypted only with the receiver's private key. For this to work it must be computationally easy for a user to generate a public and private key-pair to be used for encryption and decryption. The strength of a public key cryptography system relies on the degree of difficulty (computational impracticality) for a properly generated private key to be determined from its corresponding public key. Security then depends only on keeping the private key private, and the public key may be published without compromising security.
- Because of the computational complexity of asymmetric encryption, it is usually used only for small blocks of data, typically the transfer of a symmetric encryption key (e.g. a session key). This symmetric key is then used to encrypt the rest of the potentially long message sequence. The symmetric encryption/decryption is based on simpler algorithms and is much faster.

## Usage of public key
Two of the best-known uses of public key cryptography are:
- **Public key encryption**, in which a message is encrypted with a recipient's public key. The message cannot be decrypted by anyone who does not possess the matching private key, who is thus presumed to be the owner of that key and the person associated with the public key. This is used in an attempt to ensure confidentiality.
- **Digital signatures**, in which a message is signed with the sender's private key and can be verified by anyone who has access to the sender's public key. This verification proves that the sender had access to the private key, and therefore is likely to be the person associated with the public key. This also ensures that the message has not been tampered with, as a signature is mathematically bound to the message it originally was made with, and verification will fail for practically any other message, no matter how similar to the original message.

- An analogy to public key encryption is that of a locked mail box with a mail slot. The mail slot is exposed and accessible to the public – its location (the street address) is, in essence, the public key. Anyone knowing the street address can go to the door and drop a written message through the slot. However, only the person who possesses the key can open the mailbox and read the message.
- An analogy for digital signatures is the sealing of an envelope with a personal wax seal. The message can be opened by anyone, but the presence of the unique seal authenticates the sender.

## Problems of public generated key
- A central problem with the use of public key cryptography is confidence/proof that a particular public key is authentic, in that it is correct and belongs to the person or entity claimed, and has not been tampered with or replaced by a malicious third party. The usual approach to this problem is to use a public key infrastructure (PKI), in which one or more third parties – known as certificate authorities – certify ownership of key pairs. PGP, in addition to being a certificate authority structure, has used a scheme generally called the "web of trust", which decentralizes such authentication of public keys by a central mechanism, and substitutes individual endorsements of the link between user and public key. To date, no fully satisfactory solution to the "public key authentication problem" has been found

# RSA
- RSA is one of the first practical public-key cryptosystems and is widely used for secure data transmission. In such a cryptosystem, the encryption key is public and differs from the decryption key which is kept secret. In RSA, this asymmetry is based on the practical difficulty of factoring the product of two large prime numbers, the factoring problem. RSA is made of the initial letters of the surnames of Ron Rivest, Adi Shamir, and Leonard Adleman, who first publicly described the algorithm in 1977. 
- A user of RSA creates and then publishes a public key based on two large prime numbers, along with an auxiliary value. The prime numbers must be kept secret. Anyone can use the public key to encrypt a message, but with currently published methods, if the public key is large enough, only someone with knowledge of the prime numbers can feasibly decode the message.[2] Breaking RSA encryption is known as the RSA problem; whether it is as hard as the factoring problem remains an open question.
- RSA is a relatively slow algorithm, and because of this it is less commonly used to directly encrypt user data. More often, RSA passes encrypted shared keys for symmetric key cryptography which in turn can perform bulk encryption-decryption operations at much higher speed.

## Operation
- The RSA algorithm involves four steps: key generation, key distribution, encryption and decryption.
- RSA involves a public key and a private key. The public key can be known by everyone and is used for encrypting messages. The intention is that messages encrypted with the public key can only be decrypted in a reasonable amount of time using the private key.

# Symmetric-key algorithm
- Symmetric-key algorithms[1] are algorithms for cryptography that use the same cryptographic keys for both encryption of plaintext and decryption of ciphertext. The keys may be identical or there may be a simple transformation to go between the two keys
- The keys, in practice, represent a shared secret between two or more parties that can be used to maintain a private information link.
- This requirement that both parties have access to the secret key is one of the main drawbacks of symmetric key encryption, in comparison to public-key encryption (also known as asymmetric key encryption)

## Implementations
-  Examples of popular symmetric algorithms include Twofish, Serpent, **AES** (Rijndael), **Blowfish**, CAST5, Kuznyechik, RC4, **3DES**, Skipjack, Safer+/++ (Bluetooth), and IDEA.[5][6]


# References
- https://www.javamex.com/tutorials/cryptography/hash_functions_algorithms.shtml
- https://www.goanywhere.com/blog/2011/10/20/sftp-ftps-secure-ftp-transfers
- https://en.wikipedia.org/wiki/Secure_Shell
- https://en.wikipedia.org/wiki/Ssh-keygen
- https://en.wikipedia.org/wiki/Cryptographic_hash_function
- https://en.wikipedia.org/wiki/Rainbow_table
- https://en.wikipedia.org/wiki/Merkle%E2%80%93Damg%C3%A5rd_construction
- https://en.wikipedia.org/wiki/Public-key_cryptography
- https://en.wikipedia.org/wiki/RSA_%28cryptosystem%29

