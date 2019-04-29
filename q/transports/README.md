A transport is any mechanism that allows messages to flow.

Some transports are symmetrical and duplex. For example, a socket
allows both reading and writing over the same socket.

Other transports are asymmetric and duplex. For example, http is
duplex (data can flow both ways) -- but receiving over http requires
a web server, whereas sending over http requires quite a different
piece of software (an http client).

Other transports are simplex, meaning they only allow transmission
in one direction. SMTP is simplex (it's send-only), and so is IMAP
(receive-only). When you combine them, you get duplex capabilities, but
individually, they are simplex.

In this folder, any module that ends with `_receiver` is about
receiving data, and any that ends with `_sender` is about the
opposite. 

A __bound transport__ is one that has a predefined destination. An __unbound
transport__ can send using the same protocol, but to an arbitrary
endpoint as an arg.