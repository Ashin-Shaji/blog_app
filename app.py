#super advanced
import streamlit as st, logging, asyncio, os
from typing import Any, Dict, Type
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

os.environ["GOOGLE_API_KEY"] =
#st.secrets["GOOGLE_API_KEY"]

# Configuration Class
class Config(BaseModel):
    model_name: str = "gemini-1.5-pro-latest"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom Exception
class BlogError(Exception):
    pass

# Metaclass for Singleton Pattern
class SingletonMeta(type):
    _instances: Dict[Type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

# LLM Interface Class with Singleton Metaclass
class BlogLLM(metaclass=SingletonMeta):
    def __init__(self, model_name: str):
        self.llm = ChatGoogleGenerativeAI(model=model_name)
    
    async def generate_blog(self, prompt: str) -> str:
        try:
            logger.info("Generating blog with prompt: %s", prompt)
            response = await asyncio.to_thread(self.llm.invoke, prompt)
            return response.content
        except Exception as e:
            logger.error("Failed to generate blog content: %s", e)
            raise BlogError(f"Failed to generate blog content: {str(e)}")

# Blog Generator Class using Property Decorators and Dependency Injection
class BlogGenerator:
    def __init__(self, llm: BlogLLM, num_words: int, audience: str, topic: str):
        self.llm = llm
        self._num_words = num_words
        self._audience = audience
        self._topic = topic

    @property
    def num_words(self) -> int:
        return self._num_words

    @num_words.setter
    def num_words(self, value: int) -> None:
        if value < 50 or value > 2000:
            raise ValueError("Number of words must be between 50 and 2000")
        self._num_words = value

    @property
    def audience(self) -> str:
        return self._audience

    @audience.setter
    def audience(self, value: str) -> None:
        if value not in ["Common People", "Researchers", "Data Scientists"]:
            raise ValueError("Invalid audience type")
        self._audience = value

    @property
    def topic(self) -> str:
        return self._topic

    @topic.setter
    def topic(self, value: str) -> None:
        if not value:
            raise ValueError("Topic cannot be empty")
        self._topic = value.title()

    def create_prompt(self) -> str:
        template = f"Write a {self.num_words}-word blog for {self.audience} about {self.topic}."
        prompt = PromptTemplate(input_variables=['num_words', 'audience', 'topic'], template=template)
        return prompt.format(num_words=self.num_words, audience=self.audience, topic=self.topic)
    
    async def generate(self) -> str:
        return await self.llm.generate_blog(self.create_prompt())

# Context Manager for Streamlit Session State
class SessionStateManager:
    def __init__(self, key: str, default: Any = None):
        self.key = key
        self.default = default

    def __enter__(self):
        if self.key not in st.session_state:
            st.session_state[self.key] = self.default
        return st.session_state[self.key]

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# Decorator for UI actions
def validate_input(func):
    def wrapper(*args, **kwargs):
        ui_instance = args[0]
        if not ui_instance.topic:
            st.warning("Please enter a topic for the blog.")
            return None
        return func(*args, **kwargs)
    return wrapper

# Streamlit UI Class with Asynchronous Capabilities
class BlogGeneratorUI:
    def __init__(self, config: Config):
        self.config = config
        self.llm_interface = BlogLLM(model_name=self.config.model_name)
        self.blog_content = ""

    def render(self):
        st.title("🌟 Blog Generator 🌟")
        st.markdown("Generate well-crafted blogs with just a few clicks!")

        self.topic = st.text_input("Enter the topic for the blog:", placeholder="E.g., The future of AI")
        
        col1, col2 = st.columns([5, 5])

        with col1:
            self.num_words = st.slider("Number of words for the blog:", min_value=50, max_value=2000, step=50, value=300)
        with col2:
            self.audience = st.selectbox("Blog writing for whom?", ["Common People", "Researchers", "Data Scientists"])

        with SessionStateManager("blog_content", "") as content:
            self.blog_content = content

        if st.button("Generate Blog"):
            asyncio.run(self.generate_blog())

        if self.blog_content:
            st.subheader("📝 Generated Blog")
            st.write(self.blog_content)

            st.download_button("📥 Download Blog as Text", self.blog_content, file_name="generated_blog.txt")

    @validate_input
    async def generate_blog(self):
        try:
            blog_generator = BlogGenerator(self.llm_interface, self.num_words, self.audience, self.topic)
            self.blog_content = await blog_generator.generate()
            st.session_state.blog_content = self.blog_content
        except BlogError as e:
            st.error(str(e))
        except ValueError as e:
            st.error(str(e))

# Main Function
def main():
    config = Config()
    blog_ui = BlogGeneratorUI(config)
    blog_ui.render()

if __name__ == "__main__":
    main()
