UdpRecv
=========

This is a single file library which is handy when dissecting custom protocols over UDP. 
Given a list of ports to bind to, UdpRecv will set up sockets accordingly and proceed to trigger callbacks on every packet received.

A simple example would be to simply pretty print the contents of each packet received over a range of ports:

```
from udprecv import UdpRecv 
from pprint import pprint
recv = UdpRecv(range(1900, 1910))
test.add_callback(lambda src, msg: pprint(msg))
test.start()
test.join()
```

A reader function can be provided in order to parse the received packet data before the callback is called:

```
import json
recv = UdpRecv([666,])
test.add_reader(json.loads)
test.add_callback(lambda src, msg: json.dumps(msg))
```

For a more fleshed out example of the above use case, take a look at `jsonrecv`, a command line tool to pretty print JSON packets arriving over UDP.

When adding callbacks, a filter function can be provided to limit what incoming messages get processed. The below example calls `handle_func` whenever the JSON object has a field `type` equal to `value`: 

```
test.add_reader(json.loads)
test.add_callback(handle_func, lambda x: x.get('type') == 'value')
```

`UdpRecv` is written with IPv6 in mind, and supports IPv4 seamlessly by mapping IPv4 addresses to IPv6. By default, `UdpRecv` binds to all addresses (`::`, the IPv6 equivalent of `0.0.0.0`).
