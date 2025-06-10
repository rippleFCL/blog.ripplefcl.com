---
date: "2025-04-30T16:54:05+01:00"
draft: false
Description: A quick dive into picom animations and how i got them working using maths
params:
  image: header.png
  math: true
  tags:
  - maths
keywords:
    - blog
    - picom
    - arch
    - maths
    - animations
    - tech
    - ripple
    - ripplefcl
    - blog
    - cursed
    - human
    - being
title: Using the Power of Maths to Fix Picom Animations
---
# The Maths, The Code, and The Problem

Welcome.

I've been dabbling with [picom](https://github.com/yshui/picom) the [compositor](https://en.wikipedia.org/wiki/Compositing_manager). That means it does magic X11 things to make
your windows look nicer, such as drop shadows, transparency and, today's topic of interest, __animations__. As said in the title this is gonna involve maths and that is scary to some, but I assure you this is fun! ~~Hopefully~~.

## The Goal

During my short stint as a sane person, I began daily driving macOS insted of ArchLinux. The user experience and out-of-box experiance were good, but in the end it just wasn't for me; compared to my "tuned to my workflow" Arch setup it felt lacking.

After switching back to Arch I did miss some features, most notably the window animations and the overall "feel" of using the desktop. My aim was to bring this to my setup on Arch via picom[^1].

## The Problem

I immediately ran into problems around how picom animations for moving, resizing, and dragging windows work in bspwm[^2].

The problem is that picom doesn't have specific triggers for resizing or moving windows; it all has to be done by the same animation.

My first thought was "just use the preset animation `geometry`", which is configured like so:

```text {linenos=inline}
animations =(
    ...
    {
        triggers = [ "geometry" ];
        preset = "geometry-change";
        duration = 0.2;
    }
)
```

Now I would show you a video of the result of this, however I cannot be bothered, so I shall explain instead. This function is constant time, meaning that no matter how small the move or tiny the window geometry changes are, the animations will always last for the duration defined in the configuration.

This sounds fine, and it _is_ fine for moving window positions on screen, but it absolutely breaks when resizing windows. As you drag a window, this animation is triggered many times a second, and of course it takes _x_ seconds to finish that animation of the tiny move. This leads to resizes lagging heavily behind where your mouse is, which just looks horrible and feels mushy.

What we need is a time function that scales relative to how big the move is.

## The Code

As a precursor to the maths, we need some code.

My initial plan was to use the `geometry-change` preset. However, annoyingly, it uses `saved-image-blend`. This means it takes a screenshot of the window before the scale and fades it to the window post-scale, which leads to some very odd results, namely that the blend is very jarring if a window is being shrunk. This is a horrible effect and I'd rather skip it.

As I understand it, the reason `saved-image-blend` is implemented this way is the animations get applied _after_ the window scales or moves. If a window shrinks, this leads to the small window being stretched to play the animation, like so:

<div style="display: flex;">
    <figure>
        <video src="window_sr2.webm" width="85%" autoplay loop>
            <p>Your browser doesn't support HTML5 video. Here is a <a href="window_sr2.webm">link to the video</a> instead.</p>
        </video>
        <figcaption style="font-size: 1.5rem">With <code>saved-image-blend</code></figcaption>
    </figure>
    <figure>
        <video src="window_sr1.webm" width="85%" autoplay loop>
            <p>Your browser doesn't support HTML5 video. Here is a <a href="window_sr1.webm">link to the video</a> instead.</p>
        </video>
        <figcaption style="font-size: 1.5rem">Without <code>saved-image-blend</code></figcaption>
    </figure>
</div>

After digging around the [picom](https://github.com/yshui/picom/) source, I found the [presets config](https://github.com/yshui/picom/blob/next/data/animation_presets.conf). The `geometry-change` preset looks like this:

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

After removing the `saved-image-blend` section I have something akin to what I want, but there are still problems to solve.

## The Maths

After some thought, I came to the conclusion that this would be best solved with a distant dependant duration function. Time to deal with that pesky thing.

Before we get into the maths, it's worth mentioning that all of this was made far more difficult due to the limited set of mathematical operators provided by Picom: add (`+`), subtract (`-`), multiply (`*`), divide (`/`), and exponent (`^`). Many of the sums would've been a lot easier if we had operators such as `abs(x)` or `sqrt(x)`

First off, we need to figure out how far a given window is being moved:

```
x_diff='window-x - window-x-before'
y_diff='window-y - window-y-before'
diff='x_diff + y_diff'
```

This is a bit naive as window positions start in a corner (I can't remember which corner, but it doesn't matter). This makes calculating the move distance for windows translating away from this origin easy, but breaks for windows moving closer as the move distance is negative.

We're going to dive into some moderately complex maths now, but I'll do my best to explain as I go, so bear with me.

What we need is an `abs(x)` function. I spent a good deal of time researching how to do this. I knew I could do:

\[
abs(x) = \sqrt{x^2}
\]

But picom doesn't have a square root operator?! After a while, I realised the answer was, quite embarrassingly, staring me in the face:
\[
    \sqrt[b]{x} = x^{\frac{1}{b}}
\]

I felt so stupid only now remembering this. Raising a value to the power of a fraction is equvilent to the root with the same base as the fraction. A simple example of this is:

\[
    \sqrt{x} = x^{\frac{1}{2}}
\]

With that in mind, we can now build our own `abs(x)` function:

\[
    abs(x) = (x^2)^{\frac{1}{2}}
\]

In laymans terms, this is simple: Squaring _x_ will always yield a positive value because any positive squared is always positive, and any negative squared is also always positive. Since square root is the inverse of squared, we can now get the square root of _x_ to determine the absolute value of _x_.

My idea is to make a function that has a dead space where the animations for small moves are virtually instant, and animations for all larger moves that exceed the dead space last effectively the same amount of time.

A function that may come to mind is the sigmoid function, usually presented like so (operating on x-axis).

\[
    y = \frac{1}{1+e^{-x}}
\]

It can be refactored to remove _e_ and turned into a function. In simple terms, if we substitute _e_ for a bigger number (I chose 5), the transition becomes "steeper". You can see an example of this with the red line depicted in the figure below.

Steepening the transition reduces the already miniscule chances of encountering an abnormal animation duration (more on this later).

Anyway, the final form looks like this:

\[
    sigmoid(dist\_mov) = \frac{1}{1+5^{dist\_mov}}
\]

In this form, when _dist\_mov_ is negative, the output is effectively one, and when _dist\_mov_ is positive, it's effectively zero. This is the essence of the sigmoid function.

Now that we have a sigmoid function, we can put everything together to calculate how long an animation should last based on the distance a window is moved:

\[
\begin{aligned}
  sigmoid(dist\_mov) &= \frac{1}{1+5^{dist\_mov}} \\
abs(x) &= (x^2)^{\frac{1}{2}} \\
     anim\_time(dist\_mov) &= sigmoid(-abs(dist\_mov)) \\
\end{aligned}
\]

I lobbed my calculations into [desmos](https://www.desmos.com/calculator) for a nice visual representation:

![Our function is in red and the abs function is in black](desmos_wrong.png)

Honestly, this is not exactly what I wanted, but it makes sense. To understand why this didn't turn out as I'd hoped, let's try substituting the input value for the highest possible value of the _abs_ function (which is zero and will give the lowest sigmoid value). We'll then simplify down to a value:

\[
\begin{aligned}
sigmoid(dist\_mov) &= \frac{1}{1+5^{dist\_mov}} \\
sigmoid(0) &= \frac{1}{1+5^0} \\
sigmoid(0) &= \frac{1}{1+1} \\
sigmoid(0) &= \frac{1}{2} \\
sigmoid(0) &= 0.5
\end{aligned}
\]

The value I was hoping for here is 0, not 0.5. To achieve this, we need the _abs_ function to have a higher posible value. Remember the sigmoid function needs a positive value to return 0 (our dead space), but on our current graph, the _abs_ function is always negative. A quick way to achieve this is to just add a value (_dead\_space_) then simplify down again:

\[
\begin{aligned}
   anim\_time(dist\_mov) &= sigmoid(-abs(dist\_mov)+dead\_space) \\
   anim\_time(dist\_mov) &= sigmoid(dead\_space-abs(dist\_mov))
\end{aligned}
\]

In a visual representation, we can see a clear difference in how this affects the dead space:

![anim_time in green, modified abs in blue](desmos_correct.png)

Great success!

Essentially, when _anim\_time_ is calculated as zero, the animation duration is zero, and when it's one, the animation lasts as long as defined in `animation_target_duration` (more on this later), however when _anim\_time_ is between zero and one, the animation duration is <code><i>anim_time</i>*animation_target_duration</code>. This is what I previously referred to as an "abnormal animation duration"

After converting these calculations to a picom animation script, we get this:

```text {linenos=inline}
dead_space = 350;
animation_target_duration=0.2
x-diff-abs = "(((window-x-befor - window-x)^2)^0.5)";
y-diff-abs = "(((window-y-befor - window-y)^2)^0.5)";
anim-duration = "animation_target_duration*(1/(1+(5^(dead_space - (x-diff-abs + y-diff-abs)))))";
```

This kinda works, however I've now discovered a new issue where the `window-x` and `window-y` are relative to the top left corner of the window, which doesn't seem like a problem but consider this setup where we have a tall, very narrow window adjacent to a tall, wide window:

![Wonky wierd windows](weird_window_setup.png)

The issue is that if I were to swap these two windows' locations, our function would calculate this as a tiny move because the top left corners of the windows are not far apart. What we need to do is calculate the centre of the windows, then calculate the difference between the centre of each. Luckly this is simple and gives us our final iteration of the code:

```text {linenos=inline}
{
  triggers = [ "geometry" ];
  dead_space = 350;
  animation_target_duration=0.2
  win_x_center_before = "(window-x-before + (window-width-before / 2))"
  win_x_center_after = "(window-x + (window-width / 2))"
  win_y_center_before = "(window-y-before+(window-height-before / 2))"
  win_y_center_after = "(window-y + (window-height / 2))"
  x-diff-abs = "(((win_x_center_before - win_x_center_after)^2)^0.5)";
  y-diff-abs = "(((win_y_center_before - win_y_center_after)^2)^0.5)";
  anim-duration = "animation_target_duration*(1/(1+(5^(dead_space - (x-diff-abs + y-diff-abs)))))";

  scale-x = {
      curve = "cubic-bezier(0.33, 0, 1, 0.66)";
      duration = "anim-duration";
      start = "window-width-before / window-width";
      end = 1;
  };
  scale-y = {
      curve = "cubic-bezier(0.33, 0, 1, 0.66)";
      duration = "anim-duration";
      start = "window-height-before / window-height";
      end = 1;
  };
  shadow-scale-x = "scale-x";
  shadow-scale-y = "scale-y";
  offset-x = {
      curve = "cubic-bezier(0.33, 0, 1, 0.66)";
      duration = "anim-duration";
      start = "window-x-before - window-x";
      end = 0;
  };
  offset-y = {
      curve = "cubic-bezier(0.33, 0, 1, 0.66)";
      duration = "anim-duration";
      start = "window-y-before - window-y";
      end = 0;
  };
  shadow-offset-x = "offset-x";
  shadow-offset-y = "offset-y";
  suppressions = ["increase-opacity", "decrease-opacity"]

}
```

## Final Result

<figure>
    <video src="final.webm" width="85%" autoplay loop>
        <p>Your browser doesn't support HTML5 video. Here is a <a href="final.webm">link to the video</a> instead.</p>
    </video>
    <figcaption style="font-size: 1.5rem">The wonderful final product</figcaption>
</figure>

The code is good now. Thanks for reading!

Fin

(p.s. thank you very, very much [tig](github.com/tigattack))

[^1]: <https://wiki.archlinux.org/title/Picom>
[^2]: <https://wiki.archlinux.org/title/Bspwm>
