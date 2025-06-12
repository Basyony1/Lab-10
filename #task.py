import json
import requests
import pyttsx3
import pyaudio
import vosk
import random
from time import sleep

class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Slower, more natural speaking rate
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)  
    
    def speak(self, text, wait=False):
        """Speak with optional pause after"""
        self.engine.say(text)
        self.engine.runAndWait()
        if wait:
            sleep(0.5)

class SpeechRecognizer:
    def __init__(self, model_path):
        self.model = vosk.Model(model_path)
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        self.audio = pyaudio.PyAudio()
        self.stream = self._setup_audio_stream()
    
    def _setup_audio_stream(self):
        return self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000
        )
    
    def listen(self):
        while True:
            audio_data = self.stream.read(4000, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(audio_data):
                result = self._process_recognition_result()
                if result:
                    yield result
    
    def _process_recognition_result(self):
        result = json.loads(self.recognizer.Result())
        return result.get('text', '')

class DictionaryAPI:
    BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"
    
    def query(self, word, query_type="meaning"):
        response = requests.get(f"{self.BASE_URL}{word}")
        if response.status_code != 200:
            return None
        
        return self._parse_response(response.json(), word, query_type)
    
    def _parse_response(self, data, word, query_type):
        try:
            meanings = data[0].get('meanings', [])
            if not meanings:
                return None
                
            # Get all definitions
            all_definitions = []
            for meaning in meanings:
                for definition in meaning.get('definitions', []):
                    all_definitions.append(definition)
            
            if not all_definitions:
                return None
            
            # Select a random definition for variety
            selected = random.choice(all_definitions)
            
            handlers = {
                "meaning": lambda: f"The word {word} can mean: {selected['definition']}",
                "example": lambda: f"Example: {selected.get('example', 'No example available')}",
                "etymology": lambda: f"Origin: {data[0].get('origin', 'Origin unknown')}",
                "pronunciation": lambda: f"Pronounced: {data[0].get('phonetic', '')}",
                "all": lambda: self._format_complete_info(word, data[0])
            }
            
            return handlers.get(query_type, handlers["meaning"])()
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None
    
    def _format_complete_info(self, word, data):
        result = f"Complete information for {word}:\n"
        if 'phonetic' in data:
            result += f"Pronunciation: {data['phonetic']}\n"
        
        if 'origin' in data:
            result += f"Origin: {data['origin']}\n"
        
        for meaning in data.get('meanings', []):
            result += f"\nAs a {meaning['partOfSpeech']}:\n"
            for i, definition in enumerate(meaning.get('definitions', [])[:3], 1):
                result += f"{i}. {definition['definition']}\n"
                if 'example' in definition:
                    result += f"   Example: {definition['example']}\n"
        return result

class LanguageLearningAssistant:
    def __init__(self):
        self.tts = TextToSpeech()
        self.recognizer = SpeechRecognizer(r'A:\python\lab10\vosk-model-small-en-us-0.15')
        self.dictionary = DictionaryAPI()
        self.learning_mode = False
        self.quiz_words = []
    
    def run(self):
        self.tts.speak("Language learning assistant ready")
        self._main_loop()
    
    def _main_loop(self):
        for text in self.recognizer.listen():
            print(f"Recognized: {text}")
            self._process_command(text.lower())
    
    def _process_command(self, command_text):
        if "exit" in command_text or "quit" in command_text:
            self.tts.speak("Goodbye")
            exit()
        
        if "help" in command_text:
            self._show_help()
        elif "define" in command_text or "meaning" in command_text:
            self._handle_dictionary_query(command_text, "meaning")
        elif "example" in command_text:
            self._handle_dictionary_query(command_text, "example")
        elif "origin" in command_text or "etymology" in command_text:
            self._handle_dictionary_query(command_text, "etymology")
        elif "pronounce" in command_text or "pronunciation" in command_text:
            self._handle_dictionary_query(command_text, "pronunciation")
        elif "all about" in command_text:
            self._handle_dictionary_query(command_text, "all")
        elif "learning mode" in command_text:
            self._toggle_learning_mode()
        elif "quiz me" in command_text:
            self._start_quiz()
        else:
            self.tts.speak("I didn't understand. Say 'help' for available commands.")
    
    def _show_help(self):
        help_text = """
        Available commands:
        - Define [word]: Get the definition of a word
        - Example of [word]: Get an example sentence
        - Origin of [word]: Learn the word's etymology
        - Pronounce [word]: Hear the pronunciation
        - All about [word]: Get comprehensive information
        - Learning mode: Toggle extended explanations
        - Quiz me: Test your vocabulary
        - Exit: Quit the application
        """
        print(help_text)
        self.tts.speak("Here are the available commands. Check the console for details.")
    
    def _handle_dictionary_query(self, command_text, query_type):
        parts = command_text.split()
        keyword = {
            "meaning": "define",
            "example": "example",
            "etymology": "origin",
            "pronunciation": "pronounce",
            "all": "about"
        }[query_type]
        
        try:
            word_index = parts.index(keyword) + 1
            word = parts[word_index] if word_index < len(parts) else None
        except ValueError:
            word = None
        
        if not word:
            self.tts.speak(f"Please specify a word to {keyword}")
            return
        
        response = self.dictionary.query(word, query_type)
        if response:
            print(response)
            self.tts.speak(response)
            
            if self.learning_mode:
                self._provide_learning_tip(word)
        else:
            self.tts.speak(f"Sorry, I couldn't find information about {word}")
    
    def _provide_learning_tip(self, word):
        tips = [
            f"Try using {word} in a sentence today.",
            f"Can you think of three synonyms for {word}?",
            f"What's the opposite of {word}?",
            f"Draw a picture that represents {word} to help remember it."
        ]
        tip = random.choice(tips)
        self.tts.speak("Learning tip: " + tip, wait=True)
    
    def _toggle_learning_mode(self):
        self.learning_mode = not self.learning_mode
        status = "on" if self.learning_mode else "off"
        self.tts.speak(f"Learning mode is now {status}")
    
    def _start_quiz(self):
        self.tts.speak("Starting vocabulary quiz")
        # This would be expanded with actual quiz logic
        self.tts.speak("Quiz feature is under development")

if __name__ == "__main__":
    assistant = LanguageLearningAssistant()
    assistant.run()