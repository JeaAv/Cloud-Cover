from g4f.client import Client

# Create a function to handle user input and generate chatbot responses
def cloud_weather_chatbot(question):
    client = Client()

    # Set up the conversation history
    response = client.chat.completions.create(
    model="",  # Leave model name blank or pass an incorrect one
    messages=[{"role": "user", "content": "Test message"}]
)
    # Extract and return the chatbot's response
    return response.choices[0].message.content

# Example usage: Ask a question about cloud cover
question = "Can you explain the different types of clouds and what they indicate about the weather?"
response = cloud_weather_chatbot(question)
print(response)
