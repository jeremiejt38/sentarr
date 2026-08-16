"""Sentarr plugin system.

Plugins are Python packages that expose a ``SentarrPlugin`` subclass via the
``sentarr_plugin`` entry-point group.  At startup the plugin manager discovers,
validates and activates every installed plugin, letting it register hooks,
API routes and scheduled jobs.

Quick-start for plugin authors
------------------------------
1. Create a Python package (e.g. ``sentarr-plugin-foo``).
2. Subclass ``SentarrPlugin`` and override the lifecycle methods you need.
3. Declare the entry-point in ``pyproject.toml``::

       [project.entry-points."sentarr_plugin"]
       foo = "sentarr_plugin_foo:FooPlugin"

4. ``pip install sentarr-plugin-foo`` (or add it to extras).
"""
