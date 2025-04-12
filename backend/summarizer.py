# from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
# import asyncio
# from concurrent.futures import ThreadPoolExecutor

# # Choose your model (uncomment one)
# # MODEL_NAME = "google/pegasus-large"  # General purpose
# MODEL_NAME = "allenai/led-large-16384"  # Better for long legal docs
# # MODEL_NAME = "facebook/bart-large-cnn"  # Good for document summarization

# # Initialize model
# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
# model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# executor = ThreadPoolExecutor(1)

# def summarize_sync(text):
#     """Synchronous summarization"""
#     try:
#         # Different models may need different approaches
#         if "pegasus" in MODEL_NAME:
#             inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
#             summary_ids = model.generate(
#                 inputs["input_ids"],
#                 max_length=250,
#                 num_beams=4,
#                 early_stopping=True
#             )
#         elif "led" in MODEL_NAME:
#             inputs = tokenizer(text, return_tensors="pt", max_length=16384, truncation=True)
#             summary_ids = model.generate(
#                 inputs["input_ids"],
#                 max_length=512,
#                 num_beams=4,
#                 early_stopping=True
#             )
#         else:  # Default for BART etc
#             inputs = tokenizer([text], max_length=1024, truncation=True, return_tensors="pt")
#             summary_ids = model.generate(
#                 inputs["input_ids"],
#                 max_length=250,
#                 num_beams=4,
#                 early_stopping=True
#             )
            
#         return tokenizer.decode(summary_ids[0], skip_special_tokens=True)
#     except Exception as e:
#         raise Exception(f"Summarization error: {str(e)}")

# async def summarize(text):
#     """Asynchronous wrapper for summarization"""
#     loop = asyncio.get_event_loop()
#     return await loop.run_in_executor(executor, summarize_sync, text)


from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import asyncio
from concurrent.futures import ThreadPoolExecutor
import torch

# Model configuration
MODEL_NAME = "allenai/led-large-16384"
MAX_INPUT_LENGTH = 16384
MAX_OUTPUT_LENGTH = 512

# Lazy loading setup
model = None
tokenizer = None
executor = ThreadPoolExecutor(1)

def load_model():
    global model, tokenizer
    if model is None:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

def summarize_sync(text):
    """Synchronous summarization with LED-specific handling"""
    try:
        load_model()
        
        inputs = tokenizer(
            text,
            return_tensors="pt",
            max_length=MAX_INPUT_LENGTH,
            truncation=True
        )
        
        # LED-specific global attention
        global_attention_mask = torch.zeros_like(inputs["input_ids"])
        global_attention_mask[:, 0] = 1  # First token has global attention
        
        summary_ids = model.generate(
            inputs["input_ids"],
            max_length=MAX_OUTPUT_LENGTH,
            num_beams=4,
            early_stopping=True,
            global_attention_mask=global_attention_mask
        )
        
        return tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    except Exception as e:
        raise Exception(f"Summarization error: {str(e)}")

async def summarize(text):
    """Asynchronous wrapper for summarization"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, summarize_sync, text)