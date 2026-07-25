
from textblob import TextBlob

class Chatbot:
    def get_response(self, text):
        sentiment = TextBlob(text).sentiment.polarity

        if "hello" in text.lower():
            return "Hello! How can I help you today?"
        if "help" in text.lower():
            return "I can answer questions, analyze sentiment and maintain conversations."

        if sentiment > 0.3:
            return "I sense a positive emotion. " + "You said: " + text
        elif sentiment < -0.3:
            return "I understand your concern. Let me help you with: " + text

        return "AI Response: " + text
