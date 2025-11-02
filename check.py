import google.generativeai as genai

# Get available models
models = genai.list_models() 
print(models)
