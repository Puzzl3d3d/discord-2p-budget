# discord-2p-budget
Discord on a 2p budget (made in python)

No external modules or dependencies. All of this code should work out-of-the-box on fresh python installs. (With the potential exception of Tkinter, which may not be included)

`server.py` is what hosts the server. This is what the clients connect to. It takes an IP and a port

# To connect you *need* the correct port and ip!

If you set it up but others can't join, it could be for 1 of 2 reasons:

  1) Didn't setup the IP correctly (most likely left it as "localhost")
    
  3) Didn't setup the proper port forwarding rules for that IP and port


`client.py` is what connects to the server. This client script is fully customisable, as long as you don't mess with the socket stuff itself. All Tkinter rendering happens inside the `render` function. I recommend if you are to modify the script in any way, that is the sole function you change.

To connect properly, you need to put in the correct IP and port. If you are not on the same network as the server, the public IPv4 is needed. Otherwise, it is fine to use the private IPv4. The port number needs to be exact



