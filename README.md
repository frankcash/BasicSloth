# BasicSloth

![Sloth](http://media.giphy.com/media/s4zt0MoO4BJyU/giphy.gif)


BasicSloth came with the recognition that there needs to be an effect ground communication method for people in unstable situations. BasicSloth attempts to tackle this issue in a few ways including:
- Using technology which allows for simple PGP encryption and decryption. This allows messages to only be unlocked by those intended.
- Using cheap radio systems that cost thousands of dollars less than "safe" military methods, which may have more vulnerabilities than our system.
- Using radios that can be used on a huge variety of frequencies, preventing blockers for hindering the transferring of information.

#Implementation

Basic Sloth consists of four main components, which are:
- Data entry and encryption - This was done using TK for the gui, and Keybase for data encryption.
- Speech to Text - This was accomplished using Nuance speech to text technology.
- Sending - This was accomplished using a simple file read of the information input, as well as frequency modulation.
- Receiving - This was accomplished using GnuRadio, as well as demodulation and 'segmentation'

#Thanks

We give a special thanks to the Nuance team for their assistance with speech to text. We also give a large thanks to the FSF and the GnuRadio team for continuing to support open source tools that allowed us to continue this project.

# Resources
[From Baseband to bitstream](https://cansecwest.com/slides/2015/From_Baseband_to_bitstream_Andy_Davis.pdf)

[US Frequency Allocations](http://www.ntia.doc.gov/files/ntia/publications/2003-allochrt.pdf)

