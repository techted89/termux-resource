/**
 * Text Decoder Bookmarklet
 *
 * This script decodes text by converting numbers back to vowels.
 * The mapping is: 1->a, 2->e, 3->i, 4->o, 5->u.
 *
 * How it works:
 * 1. If you have selected text on the page, it decodes that text.
 * 2. If no text is selected, it will open a prompt asking for text to decode.
 * 3. The decoded text is displayed in an alert box.
 */

(function() {

    // The decoding map
    const numberToVowel = {
        '1': 'a',
        '2': 'e',
        '3': 'i',
        '4': 'o',
        '5': 'u'
    };

    /**
     * Decodes a string by replacing numbers with vowels.
     * @param {string} inputText The text to decode.
     * @returns {string} The decoded text.
     */
    function decodeText(inputText) {
        if (!inputText) {
            return "";
        }
        // Use a regular expression to find all numbers 1-5 and replace them
        // using the mapping function.
        return inputText.replace(/[1-5]/g, function(match) {
            return numberToVowel[match];
        });
    }

    // Get the selected text from the page.
    let selectedText = window.getSelection().toString();

    let textToDecode = "";

    // If text was selected, use it. Otherwise, prompt the user.
    if (selectedText && selectedText.trim().length > 0) {
        textToDecode = selectedText;
    } else {
        textToDecode = prompt("No text selected. Please enter the text you want to decode:");
    }

    // If the user provided text (either by selection or prompt), decode and show it.
    if (textToDecode) {
        const decodedText = decodeText(textToDecode);
        alert("Decoded Text:\n\n" + decodedText);
    }

})();