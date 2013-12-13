PacVis, A Real-Time Network Visualizer
======================================

PacVis, whose name comes from the combination of the words packet and visualization, is a real-time visualization of local wireless network traffic written entirely in the Python programming language. It is capable of detecting and differentiating between ARP, TCP, UDP, DNS, ICMP, and IGMP protocols and representing them in manner that is easily comprehended. Alongside a representation of wireless network traffic, it provides real-time parsing of unencrypted HTTP requests and replies to extract file names and images. Lastly, PacVis manages a running total of all DNS lookups that have occurred over the local wireless network.

Libraries Used
--------------
* Pynids
* Scapy
* Pydot
* PyQt4

Although airmon-ng isn't a library used to run PacVis, it is useful for setting up an interface that PacVis can sniff on.

To-Do
-----
* Rename variables to shorter, more concise names.
* Cleanly stop all running processes when the GUI closes or upon shutdown.
* Automatically detect wether scapy needs to parse radiotap headers to find ARP messages or if it can do so by applying a filter (applying a filter while capturing on an interface in monitor mode causes scapy to crash and hang).
