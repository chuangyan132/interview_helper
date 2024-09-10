from openai import OpenAI
import os

# ChatGPT初始prompt
INITIAL_PROMPT = """
you are an interviewer to apply the master thesis : Entwicklung einer Belohnungsfunktion für die Applikation einer Fahrassistenzfunktion mittels Reinforcement-Learningjob, 

you have to answer the relavant question, especially the rl, and carla simulation.

You need to answer it in english. 

The format of you answer should be:
1. answer should be simple, easy to understand, and keep the key words in beginning. 
2. the content should first start with simple content, then explained with detail. and give the example when necessary.
3. w

"""

class ChatGPTInterface:
    def __init__(self, api_key=None):
        # 如果没有提供api_key，尝试从环境变量获取
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("No API key provided. Set your OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=self.api_key)
        self.conversation_history = [{"role": "system", "content": INITIAL_PROMPT}]

    def get_response(self, user_input):
        self.conversation_history.append({"role": "user", "content": user_input})
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.conversation_history
            )
            assistant_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            return assistant_response
        except Exception as e:
            error_message = f"Error in getting ChatGPT response: {e}"
            print(error_message)
            return error_message

    def reset_conversation(self):
        self.conversation_history = [{"role": "system", "content": INITIAL_PROMPT}]

    def get_conversation_summary(self):
        summary = ""
        for message in self.conversation_history[1:]:  # Skip the system message
            role = "Interviewer" if message["role"] == "user" else "Interviewer"
            summary += f"{role}: {message['content']}\n\n"
        return summary

