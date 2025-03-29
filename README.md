# nightscout-to-datadog


OLLAMA_API_BASE=http://shitbox:11434 aider --architect --model ollama_chat/qwq --editor-model ollama_chat/qwen2.5-coder

prompt for aider:
architect> surround the while loop in nightscout_to_datadog.py with a try/except. an exception that is the result of a interrupt or a term signal should cause the program to exit with success, and log that it is doing so. any other exception should be logged, then the program should wait 60 seconds, then the while loop should continue. add any signal handlers that are appropriate to handle these concerns.