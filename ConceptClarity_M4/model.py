import json
import re
import random
from urllib import error, parse, request

model_name = "google/mt5-base"

tokenizer = None
model = None
model_error = None

REQUEST_TIMEOUT_SECONDS = 6

# Standard sets for term detection
BIOLOGY_KEYWORDS = ["cell", "dna", "gene", "protein", "organism", "bio", "உயிரியல்", "செல்கள்", "உயிரினம்", "மரபணு", "தாவர"]
PHYSICS_KEYWORDS = ["force", "energy", "gravity", "motion", "mass", "phys", "இயற்பியல்", "விசை", "ஆற்றல்", "திசைவேகம்", "விதி", "ஈர்ப்பு"]
CHEMISTRY_KEYWORDS = ["reaction", "molecule", "atom", "chemical", "catalyst", "வேதி", "மூலக்கூறு", "அணு", "தனிமம்", "கரைசல்"]

PREFERRED_RELATED_TERMS = {
    "dna": ["Gene", "Chromosome"],
    "rna": ["mRNA", "Protein synthesis"],
    "catalyst": ["Activation energy", "Reaction rate"],
    "catalysis": ["Activation energy", "Reaction rate"],
    "organism": ["Cell", "Species"],
    "photosynthesis": ["Chlorophyll", "Glucose"],
    "osmosis": ["Diffusion", "Semipermeable membrane"],
    "diffusion": ["Concentration gradient", "Kinetic energy"],
    "ecosystem": ["Biodiversity", "Food web"],
}

PREFERRED_EXAMPLES = {
    "dna": "Think of DNA like a gigantic blueprint or an instruction manual for a complex Lego set. In real life, forensic scientists use this 'manual' to solve mysteries by matching tiny biological clues to specific individuals.",
    "rna": "If DNA is the master blueprint, RNA is like a photocopied instruction sheet that workers take to the construction site. It carries specific orders to the 'protein factories' in your cell.",
    "photosynthesis": "Think of photosynthesis like a solar-powered kitchen inside a leaf. Plants take sunlight, water, and carbon dioxide, and 'cook' them into glucose (sugar) which is their food.",
    "osmosis": "Imagine a screen door that lets air through but keeps bugs out. Osmosis is like water trying to balance itself through a similar 'screen' (a membrane).",
    "diffusion": "Diffusion is like when someone opens a bottle of perfume in a room; slowly, the scent spreads out. In your body, oxygen moves from your lungs into your blood this way.",
    "catalyst": "Think of a catalyst like a GPS for a road trip. It doesn't drive the car, but it makes the journey much faster. In cars, catalytic converters speed up the removal of toxic gases.",
    "gravity": "Gravity is like an invisible elastic band that connects everything. It keeps your feet on the ground and reachable out into space to keep the Moon in orbit.",
}

LOCALIZATION = {
    "en": {
        "example_template": "Think of {term} as an essential gear in a clock. In the real world, researchers study this 'gear' to understand how systems stay in sync.",
        "chem_template": "Imagine {term} is like a secret ingredient in a recipe. In industrial chemistry, using {term} correctly makes processes much faster.",
        "phys_template": "Think of {term} like the invisible rules of a sport. Engineers use {term} to build safe structures like skyscrapers or rollercoasters.",
        "eco_template": "Imagine an ecosystem like a complex house of cards where {term} is one card. If it's removed, the whole structure could wobble.",
        "wiki_template": "To visualize {term}, think of it as a tool in a scientist's toolkit providing a clear 'lens' into the natural world.",
        "fallback_template": "Think of {term} like a puzzle piece of nature. Understanding it helps us see the 'big picture' of how science connects our lives.",
        "quiz_q1": "Based on the explanation, what is a primary characteristic of {term}?",
        "quiz_q2": "Which of these terms is directly related to the study of {term}?",
        "quiz_q3": "True or False: {term} plays a significant role in its respective scientific field.",
        "quiz_explanation_q1": "{term} is defined specifically by its role in the context provided.",
        "quiz_explanation_q2": "{concept} is a key component mentioned in the context of {term}.",
        "quiz_explanation_q3": "Scientific terms represent core concepts fundamental to understanding their fields.",
        "concept_theory": "Scientific theory",
        "ui_real_life_example": "Real-Life Example",
        "ui_quick_quiz": "Quick Quiz",
        "ui_further_learning": "📚 Further Learning Resources",
        "ui_related_terms": "Related Concepts",
        "ui_translate_to_en": "Translate to English",
        "analytics_difficulty": "Academic/Expert",
        "pool_biology": ["Mitochondria", "Homeostasis", "DNA", "RNA", "Cell", "Gene", "Species"],
        "pool_physics": ["Kinetic energy", "Quantum", "Force", "Mass", "Velocity", "Gravity", "Atom"],
        "pool_chemistry": ["Catalysis", "Molecule", "Stoichiometry", "Bond", "Oxidation", "pH", "Reaction", "Element"]
    },
    "ta": {
        "example_template": "{term} என்பதை கடிகாரத்தின் ஒரு முக்கிய இயந்திரம் அல்லது சக்கரம் என்று நினைத்துப் பாருங்கள். இது உடல் எவ்வாறு சீராக இயங்குகிறது என்பதைப் புரிந்துகொள்ள உதவுகிறது.",
        "chem_template": "{term} என்பது ஒரு செய்முறையில் உள்ள ஒரு ரகசிய மூலப்பொருள் போன்றது. இது வேதியியல் செயல்முறைகளை நாட்களிலிருந்து வினாடிகளாகக் குறைக்கும்.",
        "phys_template": "{term} என்பதை ஒரு விளையாட்டின் கண்ணுக்குத் தெரியாத விதிகளைப் போல நினைத்துப் பாருங்கள். பொறியாளர்கள் பாதுகாப்பான கட்டிடங்களை உருவாக்க இதை கணக்கிடுகிறார்கள்.",
        "eco_template": "சுற்றுச்சூழல் அமைப்பை ஒரு சீட்டுக்கட்டு வீடு போல கற்பனை செய்யுங்கள், அங்கு {term} ஒரு அத்தியாவசிய அட்டையாகும்.",
        "wiki_template": "{term} என்பதை ஒரு விஞ்ஞானியின் கருவிப்பெட்டியில் உள்ள ஒரு கருவியாகக் கருதுங்கள். இது குழப்பமான அவதானிப்புகளை தெளிவான உண்மைகளாக மாற்றுகிறது.",
        "fallback_template": "{term} என்பதை இயற்கை உலகின் ஒரு புதிர் துண்டாகக் கருதுங்கள். இது நம் அன்றாட வாழ்க்கையை இயற்கையின் விதிகளுடன் இணைக்கிறது.",
        "quiz_q1": "விளக்கத்தின் அடிப்படையில், {term} என்பதன் முதன்மையான பண்பு என்ன?",
        "quiz_q2": "இந்த சொற்களில் எது {term} பற்றிய ஆய்வோடு நேரடியாக தொடர்புடையது?",
        "quiz_q3": "சரி அல்லது தவறு: {term} அதன் அந்தந்த அறிவியல் துறையில் குறிப்பிடத்தக்க பங்கைக் கொண்டுள்ளது.",
        "quiz_explanation_q1": "விவரிக்கப்பட்டுள்ள சூழலின் மூலம் {term} சிறப்பாக வரையறுக்கப்படுகிறது.",
        "quiz_explanation_q2": "{concept} என்பது {term} தொடர்பான சூழலில் உள்ள ஒரு முக்கிய அங்கமாகும்.",
        "quiz_explanation_q3": "அறிவியல் சொற்கள் அவற்றின் துறைகளைப் புரிந்துகொள்வதற்கு அவசியமானவை.",
        "concept_theory": "அறிவியல் கோட்பாடு",
        "ui_real_life_example": "நிஜ வாழ்க்கை உதாரணம்",
        "ui_quick_quiz": "விரைவான வினாடி வினா",
        "ui_further_learning": "📚 கூடுதல் கற்றல் ஆதாரங்கள்",
        "ui_related_terms": "தொடர்புடைய கருத்துக்கள்",
        "ui_translate_to_en": "இந்த விளக்கத்தை ஆங்கிலத்தில் பார்க்க",
        "analytics_difficulty": "கல்விசார்/நிபுணர்",
        "pool_biology": ["மைட்டோகாண்ட்ரியா", "DNA", "RNA", "உயிர்மம்", "மரபணு", "சிற்றினம்", "உயிரினம்", "தாவரம்"],
        "pool_physics": ["இயக்க ஆற்றல்", "குவாண்டம்", "விசை", "நிறை", "திசைவேகம்", "ஈர்ப்பு", "அணு", "விதி"],
        "pool_chemistry": ["வினைவேக மாற்றம்", "மூலக்கூறு", "வேதிப்பிணைப்பு", "ஆக்ஸிஜனேற்றம்", "pH அளவு", "வேதிவினைகள்", "தனிமம்", "கரைசல்"]
    }
}

STOPWORDS = {
    "about", "after", "again", "also", "among", "and", "another", "are", "because",
    "been", "being", "between", "both", "can", "cells", "concept", "each", "from",
    "have", "into", "its", "more", "most", "other", "over", "such", "that", "their",
    "them", "these", "this", "those", "through", "used", "using", "very", "when",
    "which", "with", "within", "without",
    "மற்றும்", "என்பது", "ஒரு", "இந்த", "இருந்து", "ஆகும்", "உள்ளது"
}

def _clean_text(text, language='en'):
    if not text: return ""
    # 1. Strip Wikipedia headers
    text = re.sub(r"==.*?==\s*", " ", text)
    # 2. Strip citations
    text = re.sub(r"\[\d+\]", "", text)
    
    if language != 'en':
        # 3. Strip parenthetical content containing any Latin letters
        text = re.sub(r"\s*\([^)]*[A-Za-z][^)]*\)", "", text)
        # 4. Strip any word-like sequence that contains Latin letters
        # We catch standalone scientific names and titles
        text = re.sub(r"[A-Za-z0-9][A-Za-z0-9.\-']*[A-Za-z0-9.\-']*", "", text)
        # 5. Clean up residue like "=" or stray numbers or punctuation combos
        text = re.sub(r"\s+=\s+", " ", text)
        text = re.sub(r"\s*[=]\s*", " ", text)
        text = re.sub(r"\s+\.\s+", ". ", text)
        text = re.sub(r"\s*\(\s*\)", "", text) # Empty brackets
        
    return re.sub(r"\s+", " ", text).strip()

def _first_sentences(text, max_sentences=12, language='en'):
    cleaned = _clean_text(text, language)
    parts_raw = re.split(r"(?<=[.!?])\s+", cleaned)
    parts = []
    if language == 'ta':
        for p in parts_raw:
            # Only keep sentences that have Tamil content
            if any('\u0b80' <= c <= '\u0bff' for c in p):
                parts.append(p)
    else:
        parts = list(parts_raw)
    
    res_list = []
    for i in range(min(len(parts), max_sentences)):
        res_list.append(str(parts[i]))
    return " ".join(res_list).strip()

def _is_valid_related_term(candidate, term):
    if not candidate or len(candidate) > 32 or ":" in candidate: return False
    term_low = (term or "").lower()
    cand_low = candidate.lower()
    if cand_low == term_low: return False
    banned = {"help", "template", "wikipedia", "article", "page", "category"}
    return cand_low not in banned

def _http_get_json(url):
    req = request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _extract_related_terms(term, text, language='en'):
    words = re.findall(r"\b\w{4,}\b", text or "")
    candidates = []
    seen = { (term or "").lower() }
    for w in words:
        low = w.lower()
        if low in STOPWORDS or low in seen: continue
        # Strict Latin filter for non-English
        if language != 'en' and re.match(r"^[A-Za-z\s\-]+$", w) and len(w) > 3: continue
        seen.add(low)
        candidates.append(w.capitalize())
        if len(candidates) >= 4: break
    if len(candidates) < 2:
        loc = LOCALIZATION.get(language, LOCALIZATION['en'])
        return [str(loc.get("concept_theory", "Science")), "Research"]
    return candidates

def _refine_related_terms(term, candidate_terms, explanation, language='en'):
    cleaned = []
    seen = { (term or "").lower() }
    for item in (candidate_terms or []):
        cand = str(item).strip()
        if not _is_valid_related_term(cand, term): continue
        if language != 'en' and re.match(r"^[A-Za-z\s\-]+$", cand) and len(cand) > 3: continue
        if cand.lower() in seen: continue
        seen.add(cand.lower())
        cleaned.append(cand)
        if len(cleaned) >= 4: break
    
    if len(cleaned) < 4:
        fallbacks = _extract_related_terms(term, explanation, language)
        for f in fallbacks:
            if f.lower() not in seen:
                cleaned.append(f)
                seen.add(f.lower())
                if len(cleaned) >= 4: break
    return cleaned[:4]

def _real_life_example(term, explanation, source, language='en'):
    loc = dict(LOCALIZATION.get(language, LOCALIZATION['en']))
    text = (explanation or "").lower()
    if any(k in text for k in BIOLOGY_KEYWORDS):
        return str(loc.get("example_template", "")).format(term=term)
    if any(k in text for k in CHEMISTRY_KEYWORDS):
        return str(loc.get("chem_template", "")).format(term=term)
    if any(k in text for k in PHYSICS_KEYWORDS):
        return str(loc.get("phys_template", "")).format(term=term)
    return str(loc.get("fallback_template", "")).format(term=term)

def _wikipedia_explanation(term, language='en', difficulty='advanced'):
    try:
        q = parse.quote(term)
        search = _http_get_json(f"https://{language}.wikipedia.org/w/api.php?action=query&list=search&srsearch={q}&format=json")
        hits = search.get("query", {}).get("search", [])
        title = term
        if isinstance(hits, list) and len(hits) > 0:
            first_hit = hits[0]
            if isinstance(first_hit, dict):
                title = str(first_hit.get("title", term))
        
        content_url = f"https://{language}.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&format=json&titles={parse.quote(title)}"
        content = _http_get_json(content_url)
        pages = content.get("query", {}).get("pages", {})
        page = {}
        if isinstance(pages, dict) and len(pages) > 0:
            page = next(iter(pages.values()), {})
        
        extract = _first_sentences(str(page.get("extract", "")), 18 if difficulty=='advanced' else 6, language)
        if not extract: return None
        
        # Get intro links for better related terms
        intro_url = f"https://{language}.wikipedia.org/w/api.php?action=parse&prop=text&section=0&format=json&page={parse.quote(title)}"
        intro_data = _http_get_json(intro_url)
        html = intro_data.get("parse", {}).get("text", {}).get("*", "")
        links = re.findall(r'<a [^>]*title="([^"]+)"[^>]*>', html)
        
        return {
            "term": title, "explanation": extract, "source": "wikipedia",
            "related_terms": _refine_related_terms(title, links, extract, language),
            "real_life_example": _real_life_example(title, extract, "wikipedia", language)
        }
    except: return None

def _generate_quiz(term, explanation, language='en'):
    loc = dict(LOCALIZATION.get(language, LOCALIZATION['en']))
    words = re.findall(r"\b\w{5,}\b", explanation or "")
    concepts = [w for w in words if w.lower() not in STOPWORDS and w.lower() != (term or "").lower()]
    # Strict filter for quiz answers/distractors
    if language != 'en':
        concepts = [c for c in concepts if not re.match(r"^[A-Za-z]+$", c)]
    
    # Detect theme for Distractor Pool
    exp_lower = (explanation or "").lower()
    if any(k in exp_lower for k in BIOLOGY_KEYWORDS):
        pool_key = "pool_biology"
    elif any(k in exp_lower for k in PHYSICS_KEYWORDS):
        pool_key = "pool_physics"
    else:
        pool_key = "pool_chemistry"
    
    pool_raw = loc.get(pool_key, [])
    pool = []
    if isinstance(pool_raw, list):
        pool = [str(x) for x in pool_raw]
        
    final = []
    seen_final = set()
    for c in (concepts + pool):
        c_str = str(c)
        if c_str.lower() not in seen_final:
            final.append(c_str)
            seen_final.add(c_str.lower())
    
    # Safe slicing for answers
    ans_list = []
    dist_pool = []
    for idx_f, val_f in enumerate(final):
        if idx_f < 3:
            ans_list.append(val_f)
        else:
            dist_pool.append(val_f)
    if len(dist_pool) < 3: dist_pool += ["Process", "Evidence", "System"]
    
    questions = []
    for i in range(min(3, len(ans_list))):
        ans = str(ans_list[i])
        dists = random.sample(dist_pool, 3)
        opts = [ans] + dists
        random.shuffle(opts)
        questions.append({
            "question": str(loc.get(f"quiz_q{i+1}", "Question about {term}")).format(term=term),
            "options": opts, "answer": ans,
            "explanation": str(loc.get(f"quiz_explanation_q{i+1}", "Correct because of {concept}")).format(term=term, concept=ans),
            "related_concepts": dists[:2]
        })
    return { "questions": questions, "advanced_analytics": { "difficulty": str(loc.get("analytics_difficulty", "Advanced")) } }

def _fallback_explanation(term, language='en'):
    readable = (term or "").strip() or "Concept"
    if language == 'ta':
        explanation = f"{readable} என்பது ஒரு அடிப்படை அறிவியல் கருத்து ஆகும். இது இயற்கை நிகழ்வுகள் எவ்வாறு நிகழ்கின்றன என்பதை விளக்கும் ஒரு தர்க்கரீதியான கட்டமைப்பை வழங்குகிறது."
        related = ["அறிவியல்", "ஆராய்ச்சி"]
    else:
        explanation = f"{readable} is a fundamental scientific concept that provides a logical framework for understanding natural phenomena."
        related = ["Science", "Research"]
    return {
        "term": readable, "explanation": explanation, "related_terms": related,
        "real_life_example": _real_life_example(readable, explanation, "fallback", language),
        "source": "fallback"
    }

def generate_explanation(term, language='en', difficulty='advanced'):
    res = _wikipedia_explanation(term, language, difficulty)
    if not res:
        res = _fallback_explanation(term, language)
    res["quiz"] = _generate_quiz(res.get("term", term), res.get("explanation", ""), language)
    res["ui"] = dict(LOCALIZATION.get(language, LOCALIZATION['en']))
    return res