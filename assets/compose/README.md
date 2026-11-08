# Composed screenshots

`imgblock-{light,dark}.html` lay out ImgBlock's before and after captures side by
side. `imgblock-{before,after}.png` are `imgblock-*-full.png` cropped to the article
and popup (`magick … -crop 2030x1318+620+0`). Render each page at 1600×1000 into
`assets/shots/`, for example with a headless Firefox:

```sh
firefox --headless --window-size=1600,1000 --screenshot ../shots/imgblock-light.png "file://$PWD/imgblock-light.html"
```

`snipo-extension-{light,dark}.html` show a sample documentation page alongside
Snipo 2.2.1's actual save dialog. The iframe embeds `extension/styles.css`,
`extension/save/save.css` and `extension/save/save.js` from the Snipo repository.
Only `chrome.runtime.sendMessage` is replaced with fixture responses for the
draft, folders and tags. The fixture uses `docs.example.com`, performs no network
requests and has no credentials. Filename, folder and tags are prefilled as a
user would enter them; the form's native dark styling is preserved. Render at
1600×1000 using a fresh headless Firefox-family browser profile.
