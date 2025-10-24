# Text Encoder Script

This project contains a simple Python script (`encoder.py`) that encodes a given text file by replacing vowels with numbers according to a specific bijection.

## How it Works

The script reads the content from the `encode.txt` file and applies the following vowel-to-number mapping:

*   `a` or `A` is converted to `1`
*   `e` or `E` is converted to `2`
*   `i` or `I` is converted to `3`
*   `o` or `O` is converted to `4`
*   `u` or `U` is converted to `5`

All other characters remain unchanged. The script is case-insensitive regarding the vowels.

## How to Use

1.  **Prepare the input text**:
    Open the `encode.txt` file and enter the text you want to encode.

2.  **Run the script**:
    Navigate to the `text-encoder` directory in your terminal and execute the following command:
    ```bash
    python3 encoder.py
    ```

The script will then print both the original and the encoded text to the console.