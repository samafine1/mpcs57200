import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import re

# Page configuration
st.set_page_config(page_title="AI Hangman Game", page_icon="🎮", layout="centered")

# Hangman stages (ASCII art)
HANGMAN_STAGES = [
    """
       ------
       |    |
       |
       |
       |
       |
    -------
    """,
    """
       ------
       |    |
       |    O
       |
       |
       |
    -------
    """,
    """
       ------
       |    |
       |    O
       |    |
       |
       |
    -------
    """,
    """
       ------
       |    |
       |    O
       |   /|
       |
       |
    -------
    """,
    """
       ------
       |    |
       |    O
       |   /|\\
       |
       |
    -------
    """,
    """
       ------
       |    |
       |    O
       |   /|\\
       |   /
       |
    -------
    """,
    """
       ------
       |    |
       |    O
       |   /|\\
       |   / \\
       |
    -------
    """
]

# Initialize session state
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'secret_word' not in st.session_state:
    st.session_state.secret_word = ""
if 'guessed_letters' not in st.session_state:
    st.session_state.guessed_letters = set()
if 'incorrect_guesses' not in st.session_state:
    st.session_state.incorrect_guesses = []
if 'game_over' not in st.session_state:
    st.session_state.game_over = False
if 'won' not in st.session_state:
    st.session_state.won = False

def generate_word_with_ai():
    """Generate a secret word using Langchain and OpenAI"""
    try:
        # Initialize OpenAI through Langchain
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.8,
            openai_api_key=st.secrets["openai"]["api_key"]
        )
        
        # Create a prompt template
        prompt = PromptTemplate(
            input_variables=[],
            template="""Generate a single random English word for a Hangman game. 
            The word should be:
            - A common English word
            - Between 5 and 10 letters long
            - Not a proper noun
            - Suitable for all ages
            
            Respond with ONLY the word in uppercase, nothing else."""
        )
        
        # Create chain and generate word
        chain = prompt | llm
        response = chain.invoke({})
        
        # Extract content from response
        word = re.sub(r'[^A-Z]', '', response.content.strip().upper())
        
        # Validate word
        if 5 <= len(word) <= 10:
            return word
        else:
            # Fallback words if AI generates invalid word
            import random
            fallback_words = ["PYTHON", "HANGMAN", "COMPUTER", "ELEPHANT", "MOUNTAIN"]
            return random.choice(fallback_words)
            
    except Exception as e:
        st.error(f"Error generating word: {str(e)}")
        # Fallback words
        import random
        fallback_words = ["PYTHON", "HANGMAN", "COMPUTER", "ELEPHANT", "MOUNTAIN"]
        return random.choice(fallback_words)

def get_display_word():
    """Get the word with guessed letters revealed"""
    display = ""
    for letter in st.session_state.secret_word:
        if letter in st.session_state.guessed_letters:
            display += letter + " "
        else:
            display += "_ "
    return display.strip()

def check_game_status():
    """Check if game is won or lost"""
    # Check if won
    if all(letter in st.session_state.guessed_letters for letter in st.session_state.secret_word):
        st.session_state.game_over = True
        st.session_state.won = True
        return
    
    # Check if lost
    if len(st.session_state.incorrect_guesses) >= 6:
        st.session_state.game_over = True
        st.session_state.won = False
        return

def make_guess(letter):
    """Process a letter guess"""
    letter = letter.upper()
    
    if letter in st.session_state.guessed_letters:
        return
    
    st.session_state.guessed_letters.add(letter)
    
    if letter not in st.session_state.secret_word:
        st.session_state.incorrect_guesses.append(letter)
    
    check_game_status()

def reset_game():
    """Reset the game state"""
    st.session_state.game_started = False
    st.session_state.secret_word = ""
    st.session_state.guessed_letters = set()
    st.session_state.incorrect_guesses = []
    st.session_state.game_over = False
    st.session_state.won = False

# Main UI
st.title("🎮 AI Hangman Game")
st.markdown("### The AI has chosen a word. Can you guess it?")

# Start game button
if not st.session_state.game_started:
    st.markdown("---")
    st.write("Click the button below to start a new game!")
    if st.button("🎯 Start New Game", type="primary", use_container_width=True):
        with st.spinner("🤖 AI is thinking of a word..."):
            st.session_state.secret_word = generate_word_with_ai()
            st.session_state.game_started = True
            st.session_state.guessed_letters = set()
            st.session_state.incorrect_guesses = []
            st.session_state.game_over = False
            st.session_state.won = False
            st.rerun()

# Game interface
if st.session_state.game_started:
    # Create three columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Display hangman
        st.markdown("### Gallows")
        stage = min(len(st.session_state.incorrect_guesses), 6)
        st.code(HANGMAN_STAGES[stage], language=None)
        
        # Display incorrect guesses
        st.markdown("### ❌ Incorrect Guesses")
        if st.session_state.incorrect_guesses:
            st.write(", ".join(st.session_state.incorrect_guesses))
        else:
            st.write("None yet")
        
        st.markdown(f"**Attempts remaining:** {6 - len(st.session_state.incorrect_guesses)}")
    
    with col2:
        # Display word progress
        st.markdown("### 📝 Word")
        st.markdown(f"### {get_display_word()}")
        st.markdown(f"**Length:** {len(st.session_state.secret_word)} letters")
        
        # Display all guessed letters
        st.markdown("### 🔤 Guessed Letters")
        if st.session_state.guessed_letters:
            sorted_guesses = sorted(list(st.session_state.guessed_letters))
            st.write(", ".join(sorted_guesses))
        else:
            st.write("None yet")
    
    st.markdown("---")
    
    # Game over display
    if st.session_state.game_over:
        if st.session_state.won:
            st.success("🎉 Congratulations! You won!")
            st.balloons()
        else:
            st.error(f"💀 Game Over! The word was: **{st.session_state.secret_word}**")
        
        if st.button("🔄 Play Again", type="primary", use_container_width=True):
            reset_game()
            st.rerun()
    
    # Letter input (only if game is not over)
    else:
        st.markdown("### Make Your Guess")
        
        # Create alphabet buttons
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        # Split into rows
        rows = [alphabet[i:i+9] for i in range(0, 26, 9)]
        
        for row in rows:
            cols = st.columns(len(row))
            for idx, letter in enumerate(row):
                with cols[idx]:
                    # Disable button if letter already guessed
                    disabled = letter in st.session_state.guessed_letters
                    if st.button(
                        letter, 
                        key=f"btn_{letter}",
                        disabled=disabled,
                        use_container_width=True
                    ):
                        make_guess(letter)
                        st.rerun()
        
        st.markdown("---")
        
        # Alternative text input
        with st.expander("Or type a letter"):
            guess_input = st.text_input(
                "Enter a letter:",
                max_chars=1,
                key="text_guess"
            ).upper()
            
            if st.button("Submit Guess"):
                if guess_input and guess_input.isalpha():
                    make_guess(guess_input)
                    st.rerun()
                else:
                    st.warning("Please enter a valid letter")

# Sidebar with instructions
with st.sidebar:
    st.header("📖 How to Play")
    st.markdown("""
    1. Click **Start New Game** to begin
    2. The AI will generate a secret word
    3. Guess letters by clicking buttons or typing
    4. Try to reveal the word before running out of attempts
    5. You have **6 incorrect guesses** before game over
    
    **Good luck!** 🍀
    """)
    
    st.markdown("---")
    st.markdown("### ⚙️ Game Stats")
    if st.session_state.game_started:
        st.metric("Word Length", len(st.session_state.secret_word))
        st.metric("Letters Guessed", len(st.session_state.guessed_letters))
        st.metric("Incorrect Guesses", len(st.session_state.incorrect_guesses))