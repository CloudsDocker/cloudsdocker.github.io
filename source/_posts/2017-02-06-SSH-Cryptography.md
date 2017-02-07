---
layout: page
title: SSH and Cryptography
tag: 
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

# Cryptographic hash function
- A cryptographic hash function is a special class of hash function that has certain properties which make it suitable for use in cryptography. **It is a mathematical algorithm that maps data of arbitrary size to a bit string of a fixed size** (a hash function) which is designed to also be **a one-way function**, that is, a function which is infeasible to invert. The only way to recreate the input data from an ideal cryptographic hash function's output is **to attempt a brute-force search** of possible inputs to see if they produce a match. 
-  Bruce Schneier has called one-way hash functions "the workhorses of modern cryptography".[1] The input data is often called the message, and the output (the hash value or hash) is often called the message digest or simply the `digest`.
- in information-security contexts, cryptographic hash values are sometimes called (digital) fingerprints, checksums, or just hash values, even though all these terms stand for more general functions with rather different properties and purposes.

## The ideal cryptographic hash function has five main properties:
- it is deterministic so the same message always results in the same hash
- it is quick to compute the hash value for any given message
- it is infeasible to generate a message from its hash value except by trying all possible messages
- a small change to a message should change the hash value so extensively that the new hash value appears uncorrelated with the old hash value
- it is infeasible to find two different messages with the same hash value

### Illustration[edit]
- An illustration of the potential use of a cryptographic hash is as follows: Alice poses a tough math problem to Bob and claims she has solved it. Bob would like to try it himself, but would yet like to be sure that Alice is not bluffing. Therefore, Alice writes down her solution, computes its hash and tells Bob the hash value (whilst keeping the solution secret). Then, when Bob comes up with the solution himself a few days later, Alice can prove that she had the solution earlier by revealing it and having Bob hash it and check that it matches the hash value given to him before. (This is an example of a simple commitment scheme; in actual practice, Alice and Bob will often be computer programs, and the secret would be something less easily spoofed than a claimed puzzle solution).

### Applications
#### Verifying the integrity of files or messages[edit]
- An important application of secure hashes is verification of message integrity. Determining whether any changes have been made to a message (or a file), for example, can be accomplished by comparing message digests calculated before, and after, transmission (or any other event).
- For this reason, most digital signature algorithms only confirm the authenticity of a hashed digest of the message to be "signed". Verifying the authenticity of a hashed digest of the message is considered proof that the message itself is authentic.
- **MD5, SHA1, or SHA2 hashes** are sometimes posted along with files on websites or forums to allow verification of integrity.[6] This practice establishes a chain of trust so long as the hashes are posted on a site authenticated by HTTPS.

#### Password verification
- Storing all user passwords as cleartext can result in a massive security breach if the password file is compromised. One way to reduce this danger is to only store the hash digest of each password. To authenticate a user, the password presented by the user is hashed and compared with the stored hash. 
- The password is often concatenated with a random, non-secret salt value before the hash function is applied. The salt is stored with the password hash. Because users have different salts, it is not feasible to store tables of precomputed hash values for common passwords. 

## Salt (cryptography)
- In cryptography, a salt is random data that is used as an additional input to a one-way function that "hashes" a password or passphrase. Salts are closely related to the concept of nonce. The primary function of salts is to defend against dictionary attacks or against its hashed equivalent, a pre-computed rainbow table attack.[1]

Salts are used to safeguard passwords in storage. 

# Avalanche effect
- In cryptography, the avalanche effect is the desirable property of cryptographic algorithms, typically block ciphers and cryptographic hash functions wherein if when an input is changed slightly (for example, flipping a single bit) the output changes significantly (e.g., half the output bits flip). In the case of high-quality block ciphers, such a small change in either the key or the plaintext should cause a drastic change in the ciphertext. The actual term was first used by Horst Feistel,[1] although the concept dates back to at least Shannon's diffusion.
-  The SHA-1 hash function exhibits good avalanche effect. When a single bit is changed the hash sum becomes completely different. If a block cipher or cryptographic **hash function does not exhibit the avalanche effect to a significant degree, then it has poor randomization**, and thus a cryptanalyst can make predictions about the input, being given only the output. This may be sufficient to partially or completely break the algorithm. Thus, the avalanche effect is a desirable condition from the point of view of the designer of the cryptographic algorithm or device.

# References
- https://www.goanywhere.com/blog/2011/10/20/sftp-ftps-secure-ftp-transfers
- https://en.wikipedia.org/wiki/Secure_Shell
- https://en.wikipedia.org/wiki/Ssh-keygen
- https://en.wikipedia.org/wiki/Cryptographic_hash_function
