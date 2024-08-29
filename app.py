#super advanced
import streamlit as st, logging, asyncio, os
from typing import Any, Dict, Type
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

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
                error_message = f"Error creating singleton instance: {e}"
                logger.error(error_message)
                raise BlogError(error_message) from e
        return cls._instances[cls]

# LLM Interface Class with Singleton Metaclass
class BlogLLM(metaclass=SingletonMeta):
    def __init__(self, model_name: str):
        try:
            self.llm = ChatGoogleGenerativeAI(model=model_name)
        except Exception as e:
            error_message = f"Failed to initialize LLM with model '{model_name}': {e}"
            logger.error(error_message)
            raise BlogError(error_message) from e
    
    async def generate_blog(self, prompt: str) -> str:
        try:
            logger.info("Generating blog with prompt: %s", prompt)
            response = await asyncio.to_thread(self.llm.invoke, prompt)
            if not response:
                raise ValueError("LLM response is None")
            return response.content
        except ValueError as ve:
            error_message = f"Invalid response from LLM: {ve}"
            logger.error(error_message)
            raise BlogError(error_message) from ve
        except Exception as e:
            error_message = f"Failed to generate blog content: {e}"
            logger.error(error_message)
            raise BlogError(error_message) from e

# Blog Generator Class using Property Decorators and Dependency Injection
class BlogGenerator:
    def __init__(self, llm: BlogLLM, num_words: int, audience: str, topic: str):
        try:
            self.llm = llm
            self.num_words = num_words
            self.audience = audience
            self.topic = topic
        except ValueError as ve:
            error_message = f"Invalid initialization parameters: {ve}"
            logger.error(error_message)
            raise BlogError(error_message) from ve
        except Exception as e:
            error_message = f"Error initializing BlogGenerator: {e}"
            logger.error(error_message)
            raise BlogError(error_message) from e

    @property
    def num_words(self) -> int:
        return self._num_words

    @num_words.setter
    def num_words(self, value: int) -> None:
        try:
            if value < 50 or value > 5000:
                raise ValueError("Number of words must be between 50 and 5000")
            self._num_words = value
        except ValueError as ve:
            error_message = f"Invalid number of words: {ve}"
            logger.error(error_message)
            raise BlogError(error_message) from ve

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
            error_message = f"Invalid audience type: {ve}"
            logger.error(error_message)
            raise BlogError(error_message) from ve

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
            error_message = f"Invalid topic: {ve}"
            logger.error(error_message)
            raise BlogError(error_message) from ve

    def create_prompt(self) -> str:
        try:
            template = f"Write a {self.num_words}-word blog for {self.audience} about {self.topic}."
            prompt = PromptTemplate(input_variables=['num_words', 'audience', 'topic'], template=template)
            return prompt.format(num_words=self.num_words, audience=self.audience, topic=self.topic)
        except Exception as e:
            error_message = f"Failed to create prompt: {e}"
            logger.error(error_message)
            raise BlogError(error_message) from e
    
    async def generate(self) -> str:
        try:
            return await self.llm.generate_blog(self.create_prompt())
        except Exception as e:
            error_message = f"Failed to generate blog content: {e}"
            logger.error(error_message)
            raise BlogError(error_message) from e

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
            error_message = f"Failed to enter session state manager: {e}"
            logger.error(error_message)
            raise BlogError(error_message) from e

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Exception occurred in session state management: {exc_val}")

# Decorator for UI actions
def validate_input(func):
    def wrapper(*args, **kwargs):
        ui_instance = args[0]

        # Check if topic is provided
        if not ui_instance.topic:
            st.warning("Please enter a topic for the blog.")
            return None
        
        # Check if audience is selected
        if not ui_instance.audience:
            st.warning("Please select an audience for the blog.")
            return None
        
        # Check if number of words is within the valid range
        if ui_instance.num_words < 50 or ui_instance.num_words > 5000:
            st.warning("Number of words must be between 50 and 5000.")
            return None

        return func(*args, **kwargs)
    return wrapper

# Streamlit UI Class with Asynchronous Capabilities
class BlogGeneratorUI:
    def __init__(self, config: Config):
        try:
            self.config = config
            self.llm_interface = BlogLLM(model_name=self.config.model_name)
            self.blog_content = ""
        except Exception as e:
            error_message = f"Failed to initialize BlogGeneratorUI: {e}"
            logger.error(error_message)
            raise BlogError(error_message) from e

    def render(self):
        try:
            st.title("🌟 Blog Generator 🌟")
            st.markdown("Generate well-crafted blogs with just a few clicks!")

            self.topic = st.text_input("Enter the topic for the blog:", placeholder="E.g., The future of AI")
            
            col1, col2 = st.columns([5, 5])

            with col1:
                # Strictly enforce the number of words input
                self.num_words = st.number_input(
                    "Number of words for the blog:", 
                    min_value=50, 
                    max_value=5000, 
                    step=50, 
                    value=300
                )
            with col2:
                # Audience selection
                self.audience = st.selectbox(
                    "Blog writing for whom?", 
                    ["Select...", "Common People", "Researchers", "Data Scientists"]
                )
                # Make sure "Select..." doesn't count as valid selection
                if self.audience == "Select...":
                    self.audience = ""

            with SessionStateManager("blog_content", "") as content:
                self.blog_content = content

            if st.button("Generate Blog"):
                asyncio.run(self.generate_blog())

            if self.blog_content:
                st.subheader("📝 Generated Blog")
                st.write(self.blog_content)

                st.download_button("📥 Download Blog as Text", self.blog_content, file_name="generated_blog.txt")
        except ValueError as ve:
            error_message = f"Render error: {ve}"
            logger.error(error_message)
            st.error("Rendering failed due to invalid input.")
        except Exception as e:
            error_message = f"Unexpected error during render: {e}"
            logger.error(error_message)
            st.error("An unexpected error occurred during rendering.")
            raise BlogError(error_message) from e

    @validate_input
    async def generate_blog(self):
        try:
            blog_generator = BlogGenerator(self.llm_interface, self.num_words, self.audience, self.topic)
            self.blog_content = await blog_generator.generate()
            st.session_state.blog_content = self.blog_content
        except BlogError as be:
            error_message = f"Blog generation error: {be}"
            logger.error(error_message)
            st.error("Failed to generate the blog content.")
        except Exception as e:
            error_message = f"Unexpected error during blog generation: {e}"
            logger.error(error_message)
            st.error("An unexpected error occurred during blog generation.")
            raise BlogError(error_message) from e

# Main Execution Block
if __name__ == "__main__":
    try:
        config = Config()
        ui = BlogGeneratorUI(config=config)
        ui.render()
    except ValidationError as ve:
        st.error(f"Configuration validation error: {ve}")
        logger.error(f"Configuration validation error: {ve}")
    except Exception as e:
        error_message = f"Critical error in application: {e}"
        st.error(error_message)
        logger.error(error_message)
        raise BlogError(error_message) from e
