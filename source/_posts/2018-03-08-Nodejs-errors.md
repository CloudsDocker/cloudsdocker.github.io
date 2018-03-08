08/03/2018   notes

events.js:183
      throw er; // Unhandled 'error' event
      ^

Error: unable to verify the first certificate
    at TLSSocket.<anonymous> (_tls_wrap.js:1103:38)
    at emitNone (events.js:106:13)
    at TLSSocket.emit (events.js:208:7)
    at TLSSocket._finishInit (_tls_wrap.js:637:8)
    at TLSWrap.ssl.onhandshakedone (_tls_wrap.js:467:38)

==>
add following to https request options
 ,
      rejectUnauthorized: false,
        requestCert: true,
        agent: false
------
events.js:183
      throw er; // Unhandled 'error' event
      ^

Error: connect ECONNREFUSED 127.0.0.1:443
    at Object._errnoException (util.js:1022:11)
    at _exceptionWithHostPort (util.js:1044:20)
    at TCPConnectWrap.afterConnect [as oncomplete] (net.js:1182:14)
==>
in the http request, do not use 'url' but 'host' and path
host: `tracksserver.apit.ocp.bfsonlinebanking.syd.non.c1.macquarie.com`,
    port: 443,
    path: `/login`,
