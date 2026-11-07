# Composed screenshots

`imgblock-{light,dark}.html` lay out ImgBlock's before and after captures side by
side. `imgblock-{before,after}.png` are `imgblock-*-full.png` cropped to the article
and popup (`magick … -crop 2030x1318+620+0`). Render each page at 1600×1000 into
`assets/shots/`, for example with a headless Firefox:

```sh
firefox --headless --window-size=1600,1000 --screenshot ../shots/imgblock-light.png "file://$PWD/imgblock-light.html"
```
