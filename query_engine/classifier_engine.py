import os
import google.generativeai as genai
from functools import lru_cache
from dotenv import load_dotenv
# Intents
intents = {"banking": ["check_balance", "view_transactions", "find_transaction", "view_account_summary", "get_account_details", "payment_status", "get_receipt", "request_bank_statement"],
           "loan": ["loan_status", "loan_balance", "loan_next_payment", "loan_payoff_amount", "loan_payment_history", "loan_refinance_options"],
           "investment": ["investment_balance", "investment_performance", "get_quote", "dividend_schedule", "return_of_investments"],
           "insurance": ["insurance_status", "view_coverage", "claim_status"],
           "tax": ["tax_filing_status", "view_tax_deductions", "refund_status"]}


# loading the credentials and connecting to the Gemini API.

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# domain classification using llm.

@lru_cache(maxsize=128)
def classify_domain(query : str):
    prompt = f"""You are a domain classifier for financial domain classification. Your goal is to classify the user query into the most suitable or relevant domains from: banking, loan, investment, insurance, tax. 

User query: {query}

Respond only with the domain name (one word)."""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=10,
            )
        )
        domain_text = response.text.strip().lower()
        return domain_text if domain_text in ["banking", "loan", "investment", "insurance", "tax"] else None
    except Exception as e:
        print(f"Error in domain classification: {e}")
        return None

# intent classification using llm.

@lru_cache(maxsize=128)
def classify_intent(query : str, domain : str):
    if domain == None : return None
    domain_intents = intents[domain]
    prompt = f"""You are an intent classifier strictly for the domain: {domain}

Available intents:
{", ".join(domain_intents)}

Rules:
- Your job is to classify a user query into one or more intents of the above intents.
- Choose an intent **only if** the query clearly and unambiguously matches the meaning of the intent.
- If the query is vague, general, asks for definitions, or does not closely align with any intent — respond with **"unknown"**.
- Do **not** guess or infer. Be strict. Only respond with one of the following:
- An intent name from the list
- Or the word: unknown

User query: {query}

Respond only with the intent name or "unknown"."""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=15,
            )
        )
        intent = response.text.strip().lower()
        if intent == "unknown":
            return None
        else:
            return intent
    except Exception as e:
        print(f"Error in intent classification: {e}")
        return None
