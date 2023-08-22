# Ankizlet: Quizlet to Anki Converter

Ankizlet is an application that automates the conversion of flashcards from the [Quizlet](https://quizlet.com/) service into the Anki format. With Ankizlet, the conversion process becomes effortless. Simply input a list of decks you wish to convert, then take a break while Ankizlet handles the rest.

If you find Ankizlet useful and appreciate my work, you can show your support by buying me a coffee! [Buy Me a Coffee](https://www.buymeacoffee.com/lord0t)

![](https://github.com/lordot/Ankizlet/example.jpg "GUI")

## Features

- Convert an unlimited number of decks in a single operation
- Choose to save all decks in a combined file or store each deck separately (Deck per file)
- Convert password-protected decks by providing the password separated by a space from the deck's URL
- Flip the front and back sides of the cards if needed (Turn)
- Deck and card statistics are conveniently displayed at the bottom of the application screen.

## Installation

To use Ankizlet, ensure you have **Python 3.10** or higher installed on your computer.

1. Clone this repository using Git:
   ```sh
   git clone https://github.com/lordot/ankizlet.git
   cd ankizlet

2. Create a virtual environment (recommended):
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   
## Usage


1. Run **run.py**.


2. Input a list of deck URLs you want to convert, one deck in one line. If a deck is password protected, provide the password after a space.


3. Wait for some time while the decks are being downloaded. Depending on your internet quality, this process might take a while. The app displays a counter for decks and cards at the bottom.


4. Once the download is complete, you can find the deck files in the **results** folder located at the root of the Ankizlet directory.

## Roadmap
Here's what's on the horizon for Ankizlet:

- Compile the project (I'm seeking a developer for this task)
- Add the option to disable audio and images during conversion
- Enhance performance by implementing asynchronous media file downloads

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
