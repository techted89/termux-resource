# Text Decoder Bookmarklet

This is a browser bookmarklet that decodes text by converting numbers back into their corresponding vowels. It's the inverse of the encoder script.

The decoding mapping is:
*   `1` -> `a`
*   `2` -> `e`
*   `3` -> `i`
*   `4` -> `o`
*   `5` -> `u`

## How to Use

The bookmarklet is designed for convenience. When you click it:
1.  If you have any text selected on the current web page, it will decode that selected text.
2.  If you have no text selected, it will pop up a dialog box asking you to paste or type the text you want to decode.
3.  The final, decoded text will be displayed in an alert box.

---

## Installation

To use this, you need to create a new bookmark in your browser with the code below.

### Bookmarklet Code

Copy the entire line of code below:

```
javascript:(function(){const n={'1':'a','2':'e','3':'i','4':'o','5':'u'};function o(t){return t?t.replace(/[1-5]/g,function(t){return n[t]}):""}let t=window.getSelection().toString(),e="";e=t&&t.trim().length>0?t:prompt("No text selected. Please enter the text you want to decode:"),e&&alert("Decoded Text:\n\n"+o(e))})();
```

### Desktop Browser Instructions (Chrome, Firefox, etc.)

1.  Right-click your bookmarks bar and select **"Add Page..."** or **"Add Bookmark..."**.
2.  A dialog box will appear. Give the bookmark a name, for example, **"Decode Text"**.
3.  In the **URL** or **Location** field, paste the bookmarklet code you copied from above.
4.  Save the bookmark. It will now appear on your bookmarks bar, ready to use.

### Mobile Browser Instructions (iOS/Android)

Creating bookmarklets on mobile can be tricky, but here is a general method:

1.  Create a bookmark for any page (e.g., this page).
2.  Go into your browser's bookmarks, find the one you just created, and choose to **Edit** it.
3.  Change the name to something like **"Decode Text"**.
4.  Replace the contents of the **URL** or **address** field with the bookmarklet code from above.
5.  Save the changes.

You can now use it by typing the bookmark's name ("Decode Text") in your address bar and tapping the result that appears under "Bookmarks" or "History". On some mobile browsers, you can also access it directly from your bookmarks list.