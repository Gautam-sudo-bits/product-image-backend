import google.generativeai as genai

# Get available models
models = genai.list_models()  # This might list the available models depending on the SDK
print(models)
