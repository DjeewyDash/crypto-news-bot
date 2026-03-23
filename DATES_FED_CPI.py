def get_gemini_dates():
    global CACHE_DATES, LAST_UPDATE
    import re, time
    
    # Cache de 12 heures
    if time.time() - LAST_UPDATE < 43200 and CACHE_DATES["fed"] != "--":
        return CACHE_DATES

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # Prompt optimisé pour le formatage strict
    prompt = (
        "Donne la date de clôture de la prochaine FED et celle du prochain CPI. "
        "Format JSON strict: {\"fed\": \"JJ/MM (X)\", \"cpi\": \"JJ/MM (X)\"}. "
        "RÈGLES STRICTES : "
        "1. Max 12 caractères par valeur. "
        "2. Pour les jours restants, utilise 'J-n' (ex: J-10). "
        "3. Pour le jour J, utilise 'jr J'. "
        "4. Exemple attendu: '18/03 (J-10)' ou '18/03 (jr J)'. "
        "5. Pas d'autre texte que le JSON."
    )
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            raw_text = data['candidates'][0]['content']['parts'][0]['text']
            clean_text = re.search(r'\{.*\}', raw_text, re.DOTALL).group(0)
            result = json.loads(clean_text)
            
            CACHE_DATES = result
            LAST_UPDATE = time.time()
            return result
        return CACHE_DATES
    except:
        return CACHE_DATES
