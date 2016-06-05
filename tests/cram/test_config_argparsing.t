Setup

  $ . "$TESTDIR"/setup
  $ export XDG_CONFIG_HOME="$CRAMTMP"
  $ export XDG_CONFIG_DIRS="XDG_CONFIG_HOME"
  $ cg=$XDG_CONFIG_HOME/aiohex/config.ini
  $ mkdir -p $(dirname $cg)

Config is required unless one is found through XDG.

The subcommands are globbed because their order turns out to be
non-deterministic lol.

  $ aiohex-nc sessions
  usage: aiohex.py [-h] -c CONFIG {*} ... (glob)
  aiohex.py: error: argument -c/--config is required
  [2]

  $ cp $TESTCONFIG $cg
  $ sed -i 's/^model = .*$/model = empty/' $cg
  $ aiohex-nc sessions
  Session id                             Total Hits

