from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

app = FastAPI(title="SummaryFinance AI Service")

class NewsInput(BaseModel):
    title: str
    content: str
    source_name: str
    category: str

class AnalysisResult(BaseModel):
    summary: str
    sentiment_score: float
    key_points: str
    main_topics: str

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_news(news: NewsInput):
    try:
        # Create prompt for analysis
        prompt = f"""
        Analyze the following news article:
        
        Title: {news.title}
        Source: {news.source_name}
        Category: {news.category}
        
        Content:
        {news.content}
        
        Please provide:
        1. A concise summary (max 3 sentences)
        2. A sentiment score (-1 to 1, where -1 is very negative, 0 is neutral, 1 is very positive)
        3. Key points (bullet points)
        4. Main topics/themes
        
        Format the response in JSON.
        """
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        
        # Parse the response
        # Note: This is a simplified version. You might need to adjust the parsing based on actual response format
        result = response.text
        
        # For now, returning dummy data
        return AnalysisResult(
            summary="[Summary will be extracted from Gemini response]",
            sentiment_score=0.0,
            key_points="[Key points will be extracted from Gemini response]",
            main_topics="[Main topics will be extracted from Gemini response]"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
