Paramiko Shell
==============

This is a simple interactive shell written using Paramiko.

Designed for use in applications already leveraging paramiko to provide an
interactive shell in the place of OpenSSH client.
This can be preferable when Paramiko's handling of connections is likely to
mismatch with OpenSSH.


Why not use Paramiko's interactive.py demo?
-------------------------------------------

The demo code from the Paramiko project is not production quality.
It has known issues (shell history, unicode decode errors, &c) and isn't a
viable OpenSSH client replacement.

So why not make a pull request to the paramiko project?
This is a point of possible contention, but keeping this project separate and
independent from Paramiko allows for clearer SoC, at the cost of some
visibility.

`interactive.py` is clearly designed as a simple sketch of Paramiko's features,
and is intentionally kept simple and poor in features.


License and Author
------------------

License: MIT

Author: Stephen Rosen
