+++
date = '2025-04-30T16:54:05+01:00'
draft = true
title = 'Using the power of maths to fix picom'
tags = [
    "maths",
]
+++

## Intro

Welcome.

I've been dabbling with [picom](https://github.com/yshui/picom) the [compositor](https://en.wikipedia.org/wiki/Compositing_manager). That means it does magic X11 things to make
your windows look nicer, such as drop shadows, transparency and, today's topic of interest, __animations__. As said in the title this is gonna involve maths and that is scary to some
but i assure you this is fun! ~~hopfully~~.



## The picom journey begins
So to begin, after alot of tinkering with fading, transparency and the myriad of other settings in picom. One thing became
very apparent, its features wierdly conflict. good example of this is fading:

```conf
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

```conf
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

ill quickly explain whats going on here before explaing why to go the animation route insted of setting fade to true.

so the preset appear/disappear are just fading opacity of the window from 0-100 and 100-0 respectivly. so we trigger this on opening/closing a window and hiding/showing
(minimising/switching virtual desktops). the open/close/show/hide triggers mimic the fading option.
now, problems begin when i attempted to use window rules to make unfocused windows slightly transparent.

```conf
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
the main problem seams to be when the `fading` option is set there seams to be no animation on the opacity changing or when its set like this? honestly i have no clue.
the result is when a window opens its instantly focused and so no animation plays and it appears at full opacity, anyways not good :(


## Fixing the fading problems


the solution I came up with was to impliment "fading but better" myself:

```conf {linenos=inline}
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

so the main fixes is attach a fading animation to opacity changes then blocking that animation when the window open/closes/shows/hides. This looks good 10/10.

## The maths, The code and the problem

