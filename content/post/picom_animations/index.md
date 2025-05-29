+++
date = '2025-05-15T16:54:05+01:00'
draft = false
title = 'Exploring picom animations'
[params]
  math = true
image = 'header.png'
tags = [
    "maths",
]
+++


## The picom journey begins
So to begin, after a lot of tinkering with fading, transparency and the myriad of other settings in picom. One thing became
very apparent, its features weirdly conflict. Good example of this is fading:

```text {linenos=inline}
#################################
#           Fading              #
#################################

# Fade windows in/out when opening/closing and when opacity changes,
# unless no-fading-openclose is used. Can be set per-window using rules.
#
# Default: false
fading = false;

# Opacity change between steps while fading in. (0.01 - 1.0, defaults to 0.028)
fade-in-step = 0.028;

# Opacity change between steps while fading out. (0.01 - 1.0, defaults to 0.03)
fade-out-step = 0.028;

# The time between steps in fade step, in milliseconds. (> 0, defaults to 10)
fade-delta = 150

# Do not fade on window open/close.
no-fading-openclose = false

# Do not fade destroyed ARGB windows with WM frame. Workaround of bugs in Openbox, Fluxbox, etc.
# no-fading-destroyed-argb = false

```


turning this setting on seams to equate to these 'animation scripts':

```text {linenos=inline}
animations = ({
        triggers = [ "open" ];
        preset = "appear";
        duration = 0.3;
        suppressions = ["geometry"];
    },
    {
        triggers = [ "close" ];
        preset = "disappear";
        duration = 0.1;
        suppressions = ["geometry"];
    },
    {
        triggers = [ "show" ];
        preset = "appear";
        duration = 0.125;
    },
    {
        triggers = [ "hide" ];
        preset = "disappear";
        duration = 0.125;
    }
)
```

I'll quickly explain what's going on here before explaining why to go the animation route instead of just setting fade to true.

so the preset appear/disappear are just fading opacity of the window from 0-100 and 100-0 respectively. So we trigger this on opening/closing a window and hiding/showing
(minimizing/switching virtual desktops). The open/close/show/hide triggers mimic the fading option.
Now, problems begin when I attempted to use window rules to make unfocused windows slightly transparent.

```text {linenos=inline}
rules = (
    {
    match = "focused";
    opacity = 1;
    },
    {
    match = "!focused";
    opacity = 0.95;

    },
)
```
The main problem seams to be when the `fading` option is set there is no animation on the opacity changing? Honestly I have no clue.
The result is when a window opens its instantly focused and so no animation plays, and it appears at full opacity, anyway not good :(


## Fixing the fading problems


the solution I came up with was to implement "fading but better" myself:

```text {linenos=inline}
animations = ({
        triggers = [ "open" ];
        preset = "appear";
        duration = 0.3;
        suppressions = ["increase-opacity", "decrease-opacity"];
    },
    {
        triggers = [ "close" ];
        preset = "disappear";
        duration = 0.1;
        suppressions = ["increase-opacity", "decrease-opacity"];
    },
    {
        triggers = [ "show" ];
        preset = "appear";
        duration = 0.125;
        suppressions = ["increase-opacity", "decrease-opacity"]

    },
    {
        triggers = [ "hide" ];
        preset = "disappear";
        duration = 0.125;
        suppressions = ["increase-opacity", "decrease-opacity"]
    },
    {
        triggers = [ "increase-opacity", "decrease-opacity" ];
        opacity = {
            duration = 0.125;
            start = "window-raw-opacity-before";
            end = "window-raw-opacity";
        }
    },
)
```

So the main fixes are attached a fading animation to opacity changes then blocking that animation when the window open/closes/shows/hides. This looks good 10/10.
This is a big plus for doing all animations yourself none of the in built animations toggles have the suppression section, so nothing quite works correctly together
