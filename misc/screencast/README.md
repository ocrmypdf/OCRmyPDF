<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->

To regenerate
=============

Using asciinema and svg-term (`npm install -g svg-term-cli`).

Create `~/.config/asciinema/config` to disable prompt.

```
[record]

command = fish --init-command 'alias fish_prompt="echo \>\ "'
```

Run asciinema

```
asciinema rec new_input.cast
```

Re-record faster version with fewer pauses

```
asciinema rec demo.cast -c "asciinema play new_input.cast --speed 2 --idle-time-limit 0.5"
```

Convert to SVG
```
svg-term --in=misc/screencast/demo.cast --out=misc/screencast/demo.svg --window
```
