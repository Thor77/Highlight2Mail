Highlight2Mail
==============

A ZNC-Script that send you missed highlights via mail

Installation
============
Place the module in `<znc's datadir>/modules` (if not set `~/.znc/modules`).  
**Make sure the file is read- und executable by the znc's run-user.**

FAQ
====
**Why doesn't the plugin accept args in webmin?**  
*You're using the wrong ZNC-Version! This features was added to the python-bindings in version `1.5.0`!*

--

**Why doesn't the plugin show up in `listavailmods`?**  
*This module uses python-bindings! ZNC have to be compiled with `--enable-python` and the `modpython`-module have to be loaded.*
