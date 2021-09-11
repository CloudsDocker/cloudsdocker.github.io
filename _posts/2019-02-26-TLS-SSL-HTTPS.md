---
title: Awesome SSL certificates and HTTPS
date: 2020-06-26
tags:
- SSL
- HTTPS
layout: posts
---

# What's TLS
TLS (Transport Layer Security) and its predecessor, SSL (Secure Sockets Layer), are security protocols designed to secure the communication between a server and a client, for example, a web server and a browser. Both protocols are frequently referred to as SSL.

A TLS/SSL certificate (simply called SSL certificate) is required to enable SSL/TLS on your site and serve your website using the secure HTTPS protocol.

We offer different types of domain-validated SSL certificates signed by globally recognized certificate authorities.

# CA
A Certificate Authority (CA) (or Certification Authority) is an entity that issues digital certificates.

The digital certificate *certifies the ownership* of a public key by the named subject of the certificate. This allows others (relying parties) to rely upon signatures or assertions made by the private key that corresponds to the public key that is certified.

# Root certificate
In the SSL ecosystem, anyone can generate a signing key and sign a new certificate with that signature. However, that certificate is not considered valid unless it has been directly or indirectly signed by a trusted CA.

A trusted certificate authority is an entity that has been entitled to verify that someone is effectively who it declares to be. In order for this model to work, all the participants on the game must agree on a set of CA which they trust. All operating systems and most of web browsers ship with a set of trusted CAs.

The SSL ecosystem is based on a * model of trust relationship*, also called ** “chain of trust” **. When a device validates a certificate, it compares the certificate issuer with the list of trusted CAs. If a match is not found, the client will then check to see if the certificate of the issuing CA was issued by a trusted CA, and so on until the end of the certificate chain. The top of the chain, the root certificate, must be issued by a trusted Certificate Authority.

## Tips
The root certificate is generally embedded in your connected device. In the case of web browsers, root certificates are packaged with the browser software.

### To  install the Intermediate SSL certificates?

The procedure to install the Intermediate SSL certificates depends on the web server and the environment where you install the certificate.

For instance, Apache requires you to bundle the intermediate SSL certificates and assign the location of the bundle to the SSLCertificateChainFile configuration. Conversely, NGINX requires you to package the intermediate SSL certificates in a single bundle with the end-user certificate.

# SSL certificate chain
There are two types of certificate authorities (CAs): root CAs and intermediate CAs. In order for an SSL certificate to be trusted, that certificate must have been issued by a CA that is included in the trusted store of the device that is connecting.

In this model of trust relationships, a CA is a trusted third party that is trusted by both the subject (owner) of the certificate and the party relying upon the certificate.

In the context of a website, when we use the term digital certificate we often refer to SSL certificates. The CA is the authority responsible for issuing SSL certificates publicly trusted by web browsers.

Anyone can issue SSL certificates, but those certificates would not be trusted automatically by web browsers. Certificates such as these are called self-signed. The CA has the responsibility to validate the entity behind an SSL certificate request and, upon successful validation, the ability to issue publicly trusted SSL certificates that will be accepted by web browsers. Essentially, the browser vendors rely on CAs to validate the entity behind a web site.

# How SSL work in browser
There are 3 essential elements at work in the process described above: a protocol for communications (SSL), credentials for establishing identity (the SSL certificate), and a third party that vouches for the credentials (the certificate authority).


    Computers use protocols to allow different systems to work together. Web servers and web browsers rely on the Secure Sockets Layer (SSL) protocol to enable encrypted communications. The browser’s request that the server identify itself is a function of the SSL protocol.
    Credentials for establishing identity are common to our everyday lives: a driver’s license, a passport, a company badge. An SSL certificate is a type of digital certificate that serves as a credential in the online world. Each SSL certificate uniquely identifies a specific domain (such as thawte.com) and a web server.
    Our trust of a credential depends on our confidence in the organization that issued it. Certificate authorities have a variety of methods to verify information provided by individuals or organizations. Established certificate authorities, such as Thawte, are well known and trusted by browser vendors. Browsers extend that trust to digital certificates that are verified by the certificate authority.


## PKI
You are correct that SSL uses an asymmetric key pair. One public and one private key is generated which also known as public key infrastructure (PKI). The public key is what is distributed to the world, and is used to encrypt the data. Only the private key can actually decrypt the data though.

> Say we both go to walmart.com and buy stuff. Each of us get a copy of Walmart's public key to sign our transaction with. Once the transaction is signed by Walmart's public key, only Walmart's private key can decrypt the transaction. If I use my copy of Walmart's public key, it will not decrypt your transaction. Walmart must keep their private key very private and secure, else anyone who gets it can decrypt transactions to Walmart. This is why the DigiNotar breach was such a big deal


# A sample of how browser get SSL certificate


If I get an SSL certificate from a well-known provider, what does that prove about my site and how?

Here's what I know:

    Assume Alice and Bob both have public and private keys
    If Alice encrypts something with Bob's public key, she ensures that only Bob can decrypt it (using his private key)
    If Alice encrypts something with her own private key, anyone can decrypt it (using her public key), but they will know that it was encrypted by her
    Therefore, if Alice encrypts a message first with her own private key, then with Bob's public key, she will ensure that only Bob can decrypt it and that Bob will know the message is from her.

Regarding certificates, here's what I think happens (updated):

    I generate a request for a certificate. In that request, I put my public key and a bunch of information about myself.
    The certificate issuer (in theory) checks me out to make sure it knows who I am: talks to me in person, sees my driver's license, retina scan, or whatever.
    If they're satisfied, the certificate issuer then encrypts my request with their private key. Anyone who decrypts it with their public key knows that they vouch for the information it contains: they agree that the public key is mine and that the information stated is true about me. This encrypted endorsement is the certificate that they issue to me.
    When you connect to my site via https, I send you the certificate.
    Your browser already knows the issuer's public key because your browser came installed with that information.
    Your browser uses the issuer's public key to decrypt what I sent you. The fact that the issuer's public key works to decrypt it proves that the issuer's private key was used to encrypt it, and therefore, that the issuer really did create this certificate.
    Inside the decrypted information is my public key, which you now know has been vouched for. You use that to encrypt some data to send to me.



Your key theory: basically right, but authentication is usually done by encrypting a cryptographically secure hash of the data rather than the data itself.

A CA's signature on an SSL certificate should indicate that the CA has done a certain amount of diligence to ensure that the credentials on the certificate match the owner. That diligence varies, but the ultimate point is that they're saying that the certificate they signed belongs to the entity named on it.

See http://en.wikipedia.org/wiki/Digital_signature#Definition



A public key certificate is the signed combination between a public key, identifiers, and possibly other attributes. Those who sign this document effectively assert the authenticity of the binding between the public key and the identifier and these attributes, in the same way as a passport issuing authority asserts the binding between the picture and the name in a passport, as various other pieces of information (nationality, date of birth, ...).


    The private key is used for signing and deciphering/decrypting.
    The public key is used for verifying signatures and enciphering/encrypting.

public key cryptography: A class of cryptographic techniques employing two-key ciphers. Messages encrypted with the public key can only be decrypted with the associated private key. Conversely, messages signed with the private key can be verified with the public key.

It should be pointed out, along with all the other answers, that your private key is not always just one key that is used for both decrypting and signing messages. These should be two separate keys. This would create 4 keys for each person:

Public Encryption Key - Used to encrypt data to send to me.

Private Decryption Key - Used to decrypt messages that were encrypted using my Public Encryption Key.

Private Signing Key - Used to sign messages that I send to other people.

Public Verify Key - Used to verify that a message was, in fact, signed by me.


https://en.wikipedia.org/wiki/Savvis

Savvis - Wikipedia

Savvis, formerly SVVS on Nasdaq and formerly known as Savvis Communications Corporation, and, later, Savvis Inc., is a subsidiary of CenturyLink, a company headquartered in Monroe, Louisiana.[1] The company sells managed hosting and colocation services with more than 50 data centers[2] (over 2 million square feet) in North America, Europe, and Asia, automated management and provisioning systems, and information technology consulting. Savvis has approximately 2,500 unique business and government customers.[3][4]


The file extensions .CRT and .CER are interchangeable.  If your server requires that you use the .CER file extension, you can change the extension by following the steps below:

    Double-click on the yourwebsite.crt file to open it into the certificate display.
    Select the Details tab, then select the Copy to file button.
    Hit Next on the Certificate Wizard.
    Select Base-64 encoded X.509 (.CER), then Next.
    Select Browse (to locate a destination) and type in the filename yourwebsite.
    Hit Save. You now have the file yourwebsite.cer


    File extensions for cryptographic certificates aren't really as standardized as you'd expect. Windows by default treats double-clicking a .crt file as a request to import the certificate into the Windows Root Certificate store, but treats a .cer file as a request just to view the certificate. So, they're different in that sense, at least, that Windows has some inherent different meaning for what happens when you double click each type of file.

But the way that Windows handles them when you double-click them is about the only difference between the two. Both extensions just represent that it contains a public certificate. You can rename a file or use one in place of the other in any system or configuration file that I've seen. And on non-Windows platforms (and even on Windows), people aren't particularly careful about which extension they use, and treat them both interchangeably, as there's no difference between them as long as the contents of the file are correct.

*.pem, *.crt, *.ca-bundle, *.cer, *.p7b, *.p7s files contain one or more X.509 digital certificate files that use base64 (ASCII) encoding.


.DER = The DER extension is used for binary DER encoded certificates. These files may also bear the CER or the CRT extension.   Proper English usage would be “I have a DER encoded certificate” not “I have a DER certificate”.

.PEM = The PEM extension is used for different types of X.509v3 files which contain ASCII (Base64) armored data prefixed with a “—– BEGIN …” line.

.CRT = The CRT extension is used for certificates. The certificates may be encoded as binary DER or as ASCII PEM. The CER and CRT extensions are nearly synonymous.  Most common among *nix systems


CER = alternate form of .crt (Microsoft Convention) You can use MS to convert .crt to .cer (.both DER encoded .cer, or base64[PEM] encoded .cer)  The .cer file extension is also recognized by IE as a command to run a MS cryptoAPI command (specifically rundll32.exe cryptext.dll,CryptExtOpenCER) which displays a dialogue for importing and/or viewing certificate contents.

.KEY = The KEY extension is used both for public and private PKCS#8 keys. The keys may be encoded as binary DER or as ASCII PEM.

The only time CRT and CER can safely be interchanged is when the encoding type can be identical.  (ie  PEM encoded CRT = PEM encoded CER)


What is the SSL Certificate Chain?

There are two types of certificate authorities (CAs): root CAs and intermediate CAs. In order for an SSL certificate to be trusted, that certificate must have been issued by a CA that is included in the trusted store of the device that is connecting.



Good. I see you want to access this particular page.  I need to send the page to you in a secure way. If I
encrypt it using my public key, you won't be able to decrypt it because you don't have my private key. And since you don't have any public key of your own that I can use to encrypt the page for you here's what I propose
Since you can send me encrypted messages that only me can read (you have my public key), send me an encrypted message with an encryption key in it. Just make up a random encryption key that we'll both use to encrypt and decrypt the messages between us during this session .

A simple symmetric key is enought. We'll use the same key to encrypt and decrypt the messages.


- So there's no way that anybody with your public
key can trick others to believe that he is you ?
- Nope. That's the beauty of the assymetric encryption.


When you send the public key to the victim's contain your public key + a certificate that this public key belongs to you. If you are a website, then the certificate will contain the domain name of the website. Basically, a certificate says something like:  the following public key "XYZ123" belongs to example.com.


that's why we have "Certificate Authorities" like Verisign, Digicert or even Symantec. It is believed that these companies have the necessary trustworthiness to deliver certificates to different •entities.
Think of a CA like a registrar for public keys. Just like registrars assert that a domain name belongs to a certain person or company, CAS assert that a public key belongs to a certain domain name (or IP address) .


The certificate will contain the CA that delivered it, but you don't even have to check with them because the certificate is signed by them. That signature alone is enough proof that the certificate comes from them.


A signature is simply a small message that is encrypted with their private key. Since private keys are asymetric, that means that only the associated public key can decrypt it.

Asymmetric encryption works in both way. public -> private and private -> public.
What the public key encrypts only the private key can decrypt, and what the private key can encrypt only the public key can decrypt.



for PKI, we're not looking for secrecy here, we only want to prove that we' re the real authors of the message. Suppose I send you the message "HELLO WORLD", encrypted with my private key. The encrypted message would be, for example, "XYZ1234". So you receive "XYZ1234" . If I give you my public key, you would be able to decrypt "XYZ1234" into "HELLO WORLD" . And by doing so, you would have proof that that message was sent by me, because the public key you used decrypts messages that were encrypted by my private key only. And since I am the only person in the universe who has that private key, that proves that I am the author of that message.


Really nice. So I don't have to contact the CA to check the validity of the certificate, all I have to do is use their public key to decrypt the signature that's in it. If it's the same as err, wait, what should I compare the decrypted signature to again ?




You have to find the same hash as the one you have calculated. They are sending a small hash of the whole certificate. So what you have to do is to calculate the hash of the certificate yourself, then compare it to the hash you get when you decrypt the signature. If the two are the same that means two things
1. The CA's public key worked, so the signature was encrypted by the associated private key, which means the certificate was really issued by the CA.
2. Since the hash is the same, it also means that you are seeing the exact same certificate that the CA delivered to the website you are visiting. The information contained inside hasn't been tampered with.

That's really good. So, let me recap one more time .
1. I contact you for an HTTPS page.
2. You send me an SSL certificate that contains your public key and a signature from the CA that delivered
3. I make sure the certificate is valid by using the CA's public key to decrypt the signature. In parallel, I also calculate the hash of the certificate.

If my hash and the one I got from decrypting the signature are equal, that means that the certificate was really issued by the CA and that I can be sure that the public key you sent me is really yours.

Because you implicitly trust the CA.

Let's continue:
4. I generate a random key that we'll both use as a symmetric key to encrypt and decrypt the messages we'll be sending each other.
5. I encrypt this symmetric key with your public key and send it to you.
6. You decrypt my message with your private key and find my secret key.
7. Every request or response between us will be encrypted with this shared secret symmetric key.

## CN
The Common Name (AKA CN) represents the server name protected by the SSL certificate.

The certificate is valid only if the request hostname matches the certificate common name.

To check the status, such as
```bash
sudo openssl x509 -noout -in xxx.com.cer -text
```
 Subject: C=UK, ST=London, L=London, O=AAA Bank, OU=Product and Markets, CN=*.xxxtest.com
        Subject Public Key Info:

### commonName format

The common name is not a URL. It doesn’t include any protocol (e.g. http:// or https://), port number, or pathname. For instance, https://example.com or example.com/path are incorrect. In both cases, the common name should be example.com


#### Common Name vs Subject Alternative Name

The common name can only contain up to one entry: either a wildcard or non-wildcard name. It’s not possible to specify a list of names covered by an SSL certificate in the common name field.

The Subject Alternative Name extension (also called Subject Alternate Name or SAN) was introduced to solve this limitation. The SAN allows issuance of multi-name SSL certificates.



# SHA-2 SSL Certificates
Almost all certificates are currently signed with the SHA-2 hash algorithm.

This article provides a simple overview of the SHA-1 to SHA-2 transition plans, as well additional informations on the SHA-2 hash algorithm and SSL certificates purchased with DNSimple previous than September 2014.

The SHA family of hashing algorithms were developed by the National Institute of Standards and Technology (NIST) and are used by certificate authorities (CAs) when digitally signing issued certificates.



# Reference
- https://support.dnsimple.com/articles/what-is-ssl-certificate-chain/
- https://www.thawte.com/resources/getting-started/how-ssl-works/
