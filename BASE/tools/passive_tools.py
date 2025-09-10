def summarize_speech_queue(speech_texts: List[str], model: str) -> str:
    """Summarize and clean up speech-to-text input using Ollama"""
    if not speech_texts:
        return ""
    
    combined_text = " ".join(speech_texts)
    
    summarizer_prompt = f"""You are a speech-to-text summarizer. Your job is to:
1. Clean up any speech-to-text errors and typos
2. Combine fragmented sentences into coherent thoughts
3. Remove filler words and repetitions
4. Preserve the original meaning and intent
5. Format the result as a clear, concise summary

Original speech-to-text input: {combined_text}

Provide a clean, coherent summary of what the user said:"""
    
    messages = [
        {"role": "system", "content": "You are a helpful speech-to-text summarizer that cleans up and organizes spoken input."},
        {"role": "user", "content": summarizer_prompt}
    ]
    
    try:
        summary = chat_with_ollama(model, messages)
        return summary.strip()
    except Exception as e:
        print(errorTColor + f"[error] Summarization failed: {e}" + resetTColor)
        return combined_text  # Return original if summarization fails
    

def evaluate_search_need(summary: str, model: str) -> tuple[bool, str]:
    """Determine if a web search would be beneficial and extract search query"""
    
    evaluation_prompt = f"""Analyze the following user input summary and determine if the user would benefit from a web search.

User summary: {summary}

A search should be conducted if the user:
- Has a direct question about facts, current events, or specific information
- Expresses uncertainty or mentions not knowing something
- Asks about recent developments, news, or current status of something
- Needs factual information that isn't common knowledge
- Asks "what is", "how does", "when did", "who is", etc.

Respond with EXACTLY this format:
SEARCH_NEEDED: [YES/NO]
QUERY: [if YES, provide a concise 2-6 word search query; if NO, write "NONE"]

Examples:
- "I wonder what the weather will be like tomorrow" → SEARCH_NEEDED: YES, QUERY: weather forecast tomorrow
- "I'm not sure who won the game last night" → SEARCH_NEEDED: YES, QUERY: game results last night
- "I had a great day at work today" → SEARCH_NEEDED: NO, QUERY: NONE"""

    messages = [
        {"role": "system", "content": "You are a search evaluation assistant that determines when web searches would be helpful."},
        {"role": "user", "content": evaluation_prompt}
    ]
    
    try:
        response = chat_with_ollama(model, messages)
        lines = response.strip().split('\n')
        
        search_needed = False
        search_query = ""
        
        for line in lines:
            if line.startswith("SEARCH_NEEDED:"):
                search_needed = "YES" in line.upper()
            elif line.startswith("QUERY:"):
                query_part = line.split("QUERY:", 1)[1].strip()
                if query_part != "NONE":
                    search_query = query_part
        
        return search_needed, search_query
        
    except Exception as e:
        print(errorTColor + f"[error] Search evaluation failed: {e}" + resetTColor)
        return False, ""
    
def summarize_search_results(search_results: List[Dict[str, str]], query: str, model: str) -> str:
    """Summarize web search results into key points"""
    # return query #BYPASS SEARCH SUMM
    if not search_results:
        return "No relevant search results found."
    
    # Format results for summarization
    results_text = ""
    for i, result in enumerate(search_results, 1):
        results_text += f"{i}. {result['title']}: {result['snippet']}\n"
    
    summarizer_prompt = f"""Summarize the following web search results for the query "{query}".

Search Results:
{results_text}

Provide a concise summary that:
1. Highlights the most relevant and important information
2. Answers the user's implied question if possible
3. Mentions any conflicting information if present
4. Keeps the summary under 150 words
5. Uses clear, conversational language

Summary:"""

    messages = [
        {"role": "system", "content": "You are a web search summarizer that distills search results into key insights."},
        {"role": "user", "content": summarizer_prompt}
    ]
    
    try:
        summary = chat_with_ollama(model, messages)
        return summary.strip()
    except Exception as e:
        print(errorTColor + f"[error] Search results summarization failed: {e}" + resetTColor)
        return format_search_results(search_results)  # Fallback to raw results