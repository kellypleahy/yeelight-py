# yeelight-py
Python library for interacting with yeelight lights.

This is a sample library of how to communicate with yeelight devices on the LAN.

In order to use it currently, you must have discovered the IP address of your device already (easily done with your router, probably).
You must also have enabled LAN control on the device.

I've tested on windows with a yeelight smart lamp D2, but the protocol is basically the same for all their devices so it should be easy to add commands for other devices if they aren't supported currently.

There is very little error handling in the communications currently - on the other hand, there is lots of checking to make sure arguments and such are correct so developer mistakes are avoided for simple api behavior.

Feel free to ping me if you want to try using this or extending it.  I've built it for a small project with my family at home.
