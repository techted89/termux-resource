import os

def encode_text(input_text):
    """
    Encodes a given text by replacing vowels with numbers.
    a -> 1, e -> 2, i -> 3, o -> 4, u -> 5
    The replacement is case-insensitive.
    """
    vowel_map = {
        'a': '1', 'e': '2', 'i': '3', 'o': '4', 'u': '5',
        'A': '1', 'E': '2', 'I': '3', 'O': '4', 'U': '5'
    }

    encoded_chars = []
    for char in input_text:
        encoded_chars.append(vowel_map.get(char, char))

    return "".join(encoded_chars)

def main():
    """
    Main function to read the input file, encode its content,
    and print the result.
    """
    input_file_path = os.path.join(os.path.dirname(__file__), 'encode.txt')

    try:
        with open(input_file_path, 'r') as f:
            original_text = f.read()

        encoded_text = encode_text(original_text)

        print("Original Text:")
        print(original_text)
        print("\nEncoded Text:")
        print(encoded_text)

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file_path}'")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()