document.addEventListener('DOMContentLoaded', () => {
    // Get references to all the necessary DOM elements
    const inputText = document.getElementById('inputText');
    const outputText = document.getElementById('outputText');
    const convertBtn = document.getElementById('convertBtn');
    const encodeMode = document.getElementById('encodeMode');
    const decodeMode = document.getElementById('decodeMode');

    // Mappings for encoding and decoding
    const vowelToNumber = { 'a': '1', 'e': '2', 'i': '3', 'o': '4', 'u': '5' };
    const numberToVowel = { '1': 'a', '2': 'e', '3': 'i', '4': 'o', '5': 'u' };

    /**
     * Encodes text by replacing vowels with numbers (case-insensitive).
     * @param {string} text - The input string.
     * @returns {string} - The encoded string.
     */
    function encodeText(text) {
        return text.replace(/[aeiou]/gi, (match) => {
            return vowelToNumber[match.toLowerCase()];
        });
    }

    /**
     * Decodes text by replacing numbers with vowels.
     * @param {string} text - The input string.
     * @returns {string} - The decoded string.
     */
    function decodeText(text) {
        return text.replace(/[1-5]/g, (match) => {
            return numberToVowel[match];
        });
    }

    // Add a click event listener to the convert button
    convertBtn.addEventListener('click', () => {
        const text = inputText.value;
        let result = '';

        // Check which mode is selected and call the appropriate function
        if (encodeMode.checked) {
            result = encodeText(text);
        } else {
            result = decodeText(text);
        }

        // Display the result in the output text area
        outputText.value = result;
    });
});