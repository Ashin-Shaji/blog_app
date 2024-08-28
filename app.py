#super advanced
import streamlit as st, logging, asyncio, os
from typing import Any, Dict, Type
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

#os.environ["GOOGLE_API_KEY"] = 'AIzaSyBbepUh8x3CqpkxNFnJ1IX0dFc0UNTwwbU'
os.environ["GOOGLE_API_KEY"] = st.secrets(["GOOGLE_API_KEY"])

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
            try:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            except Exception as e:
                logger.error("Error creating singleton instance: %s", e)
                raise BlogError("Singleton instance creation failed") from e
        return cls._instances[cls]

# LLM Interface Class with Singleton Metaclass
class BlogLLM(metaclass=SingletonMeta):
    def __init__(self, model_name: str):
        try:
            self.llm = ChatGoogleGenerativeAI(model=model_name)
        except Exception as e:
            logger.error("Failed to initialize LLM with model: %s", e)
            raise BlogError("Failed to initialize LLM") from e
    
    async def generate_blog(self, prompt: str) -> str:
        try:
            logger.info("Generating blog with prompt: %s", prompt)
            response = await asyncio.to_thread(self.llm.invoke, prompt)
            if not response:
                raise ValueError("LLM response is None")
            return response.content
        except ValueError as ve:
            logger.error("Invalid response from LLM: %s", ve)
            raise BlogError("Invalid response from LLM") from ve
        except Exception as e:
            logger.error("Failed to generate blog content: %s", e)
            raise BlogError("Failed to generate blog content") from e

# Blog Generator Class using Property Decorators and Dependency Injection
class BlogGenerator:
    def __init__(self, llm: BlogLLM, num_words: int, audience: str, topic: str):
        try:
            self.llm = llm
            self.num_words = num_words
            self.audience = audience
            self.topic = topic
        except ValueError as ve:
            logger.error("Invalid initialization parameters: %s", ve)
            raise BlogError("Initialization of BlogGenerator failed") from ve
        except Exception as e:
            logger.error("Error initializing BlogGenerator: %s", e)
            raise BlogError("Initialization of BlogGenerator failed") from e

    @property
    def num_words(self) -> int:
        return self._num_words

    @num_words.setter
    def num_words(self, value: int) -> None:
        try:
            if value < 50 or value > 2000:
                raise ValueError("Number of words must be between 50 and 2000")
            self._num_words = value
        except ValueError as ve:
            logger.error("Invalid number of words: %s", ve)
            raise BlogError("Number of words out of range") from ve

    @property
    def audience(self) -> str:
        return self._audience

    @audience.setter
    def audience(self, value: str) -> None:
        try:
            if value not in ["Common People", "Researchers", "Data Scientists"]:
                raise ValueError("Invalid audience type")
            self._audience = value
        except ValueError as ve:
            logger.error("Invalid audience type: %s", ve)
            raise BlogError("Invalid audience type") from ve

    @property
    def topic(self) -> str:
        return self._topic

    @topic.setter
    def topic(self, value: str) -> None:
        try:
            if not value:
                raise ValueError("Topic cannot be empty")
            self._topic = value.title()
        except ValueError as ve:
            logger.error("Invalid topic: %s", ve)
            raise BlogError("Invalid topic") from ve

    def create_prompt(self) -> str:
        try:
            template = f"Write a {self.num_words}-word blog for {self.audience} about {self.topic}."
            prompt = PromptTemplate(input_variables=['num_words', 'audience', 'topic'], template=template)
            return prompt.format(num_words=self.num_words, audience=self.audience, topic=self.topic)
        except Exception as e:
            logger.error("Failed to create prompt: %s", e)
            raise BlogError("Failed to create prompt") from e
    
    async def generate(self) -> str:
        try:
            return await self.llm.generate_blog(self.create_prompt())
        except Exception as e:
            logger.error("Failed to generate blog content: %s", e)
            raise BlogError("Blog generation failed") from e

# Context Manager for Streamlit Session State
class SessionStateManager:
    def __init__(self, key: str, default: Any = None):
        self.key = key
        self.default = default

    def __enter__(self):
        try:
            if self.key not in st.session_state:
                st.session_state[self.key] = self.default
            return st.session_state[self.key]
        except Exception as e:
            logger.error("Failed to enter session state manager: %s", e)
            raise BlogError("Session state management failed") from e

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error("Exception occurred in session state management: %s", exc_val)

# Decorator for UI actions
def validate_input(func):
    def wrapper(*args, **kwargs):
        try:
            ui_instance = args[0]
            if not ui_instance.topic:
                st.warning("Please enter a topic for the blog.")
                return None
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("Error in input validation: %s", e)
            st.error("Input validation failed.")
            raise BlogError("Input validation failed") from e
    return wrapper

# Streamlit UI Class with Asynchronous Capabilities
class BlogGeneratorUI:
    def __init__(self, config: Config):
        try:
            self.config = config
            self.llm_interface = BlogLLM(model_name=self.config.model_name)
            self.blog_content = ""
        except Exception as e:
            logger.error("Failed to initialize BlogGeneratorUI: %s", e)
            raise BlogError("UI initialization failed") from e

    def render(self):
        try:
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
        except ValueError as ve:
            logger.error("Render error: %s", ve)
            st.error("Rendering failed due to invalid input.")
        except Exception as e:
            logger.error("Unexpected error during render: %s", e)
            st.error("An unexpected error occurred during rendering.")
            raise BlogError("Rendering failed") from e

    @validate_input
    async def generate_blog(self):
        try:
            blog_generator = BlogGenerator(self.llm_interface, self.num_words, self.audience, self.topic)
            self.blog_content = await blog_generator.generate()
            st.session_state.blog_content = self.blog_content
        except BlogError as be:
            logger.error("Blog generation error: %s", be)
            st.error("Failed to generate the blog.")
        except Exception as e:
            logger.error("Unexpected error during blog generation: %s", e)
            st.error("An unexpected error occurred while generating the blog.")
            raise BlogError("Blog generation failed") from e

# Main Function
def main():
    try:
        config = Config()
        blog_ui = BlogGeneratorUI(config)
        blog_ui.render()
    except ValidationError as ve:
        logger.error("Configuration validation error: %s", ve)
        st.error("Configuration is invalid. Please check your settings.")
    except BlogError as be:
        logger.error("Application error: %s", be)
        st.error("The application encountered an error.")
    except Exception as e:
        logger.error("Unexpected error in main: %s", e)
        st.error("An unexpected error occurred.")
        raise

if __name__ == "__main__":
    main()
