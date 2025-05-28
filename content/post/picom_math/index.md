+++
date = '2025-04-30T16:54:05+01:00'
draft = false
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

ill quickly explain whats going on here before explaing why to go the animation route insted of setting fade to true.

so the preset appear/disappear are just fading opacity of the window from 0-100 and 100-0 respectivly. so we trigger this on opening/closing a window and hiding/showing
(minimising/switching virtual desktops). the open/close/show/hide triggers mimic the fading option.
now, problems begin when i attempted to use window rules to make unfocused windows slightly transparent.

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
the main problem seams to be when the `fading` option is set there seams to be no animation on the opacity changing or when its set like this? honestly i have no clue.
the result is when a window opens its instantly focused and so no animation plays and it appears at full opacity, anyways not good :(


## Fixing the fading problems


the solution I came up with was to impliment "fading but better" myself:

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

so the main fixes is attach a fading animation to opacity changes then blocking that animation when the window open/closes/shows/hides. This looks good 10/10.
This is a big plus for doing all animations yourself non of the in built animations toggles have the suppression section so nothing quite works correctly together

# The maths, The code and the problem

## The problem

so the problem i ran into and why im writing this blog post is picom animations for moving, resizing, and dragging windows in bspwm.
now this sounds easy till you realise picom dosnt have specific triggers for resizing or moving windows, it all has to be done by the same animation.

so my first thought was just use the preset animation `geometry`:

```text {linenos=inline}
animations =(
    ...
    {
        triggers = [ "geometry" ];
        preset = "geometry-change";
    }
)
```

Now i would show you a video of the result of this, however i cannot be bothered so i shall explain instead. so this function is constant time no matter how small the move or tiny the window geometry changes it will always take how ever long you tell it.

this sounds fine and it is for moving window positions on screen. but it absoulty breaks resizing windows. as you drag a window it triggers this animation many times a second and of course it take x amount of seconds to finish that animation of the tiny move. this leads to resizing lagging heavily behind where your mouse is, it just looks horrible and feels mushy.

What we need is a time funtion that scales relative to how big the move is.

## The code

so as a precursor to the math we need some code. i was going to use the `geometry-change` preset, but it annoys me. It takes a screenshot
and shows that the window scales. it leads to some very odd results. from what i gather this is needed as the animations get applyed after the window scales/moves so if a window moves from big to small it will, shrink, scale then move. the issue is, the 'solution' is just the original problem just in the opposite direction, so id rather skip this.

so after digging around the [picom](https://github.com/yshui/picom/) i found the [presets](https://github.com/yshui/picom/blob/next/data/animation_presets.conf) config. the `geometry-change` looks like this:

```text {linenos=inline}
geometry-change = {
    scale-x = {
        curve = "cubic-bezier(0.07, 0.65, 0, 1)";
        duration = "placeholder0";
        start = "window-width-before / window-width";
        end = 1;
    };
    scale-y = {
        curve = "cubic-bezier(0.07, 0.65, 0, 1)";
        duration = "placeholder0";
        start = "window-height-before / window-height";
        end = 1;
    };
    shadow-scale-x = "scale-x";
    shadow-scale-y = "scale-y";
    offset-x = {
        curve = "cubic-bezier(0.07, 0.65, 0, 1)";
        duration = "placeholder0";
        start = "window-x-before - window-x";
        end = 0;
    };
    offset-y = {
        curve = "cubic-bezier(0.07, 0.65, 0, 1)";
        duration = "placeholder0";
        start = "window-y-before - window-y";
        end = 0;
    };
    saved-image-blend = {
        duration = "placeholder0";
        start = 1;
        end = 0;
    };
    shadow-offset-x = "offset-x";
    shadow-offset-y = "offset-y";
    *knobs = {
        duration = 0.4;
    };
    *placeholders = ((0, "duration"));
};
```

so after removing the `saved-image-blend` section i have something akin to what i want but there is still a issue

<!-- ## The maths

now to address the problem, that pesky distant dependant duration function.

so picom  -->
