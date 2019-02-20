# q
Q supplied James Bond and other secret agents with cool gadgets:

[![Q in James Bond - Towpilot BY CC 3.0](q.jpg)](https://en.wikipedia.org/wiki/Q_(James_Bond)#/media/File:Desmond_Llewelyn_01.jpg)

This repo is a source of cool agent gadgets as well, but they are
for Indy-style [self-sovereign identity agents](
https://github.com/hyperledger/indy-hipe/blob/4696f1621c7fdb1c357a4003986d92a6e1fb3256/text/0002-agents/README.md)
(much cooler than 007 :-).

Q's gadgets may be especially helpful in testing and development.
They include:

### mailagent
An agent that uses SMTP and IMAP as its transports is a useful
way to experiment with something other than HTTP. It makes
the asynchronous nature of DID Communication very obvious. And
the best part is, you don't even have to run one to use one--there's
an instance of this agent running at indyagent1@gmail.com.
Send it an email and see what happens.

### fileagent
An agent that interacts by reading and writing files in a folder
in the filesystem is a useful way to simulate arbitrary behavior
of other agents. Observe what your agent is sending by watching
a folder. Take as long as you like to build any message you
want, drop it in that folder as a response, and see how your
agent reacts. Record and playback agent behaviors by doing
simple file I/O.

### polyrelay
A pluggable relay that lets you translate any agent transport
into different transports (either 1-to-1, or teeing 1-to-many),
for arbitrary testing scenarios.
