import json
import re
import random
from urllib import error, parse, request, response
from prompt import build_prompt

model_name = "google/mt5-base"

tokenizer = None
model = None
model_error = None

REQUEST_TIMEOUT_SECONDS = 6

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
    "dna": "Think of DNA like a gigantic blueprint or an instruction manual for a complex Lego set. Just as a manual tells you exactly where every brick goes to build a castle, DNA contains the code that tells your body how to build everything from your eyes to your heartbeat. In real life, forensic scientists use this 'manual' to solve mysteries by matching tiny biological clues to specific individuals.",
    "rna": "If DNA is the master blueprint locked in a safe, RNA is like a photocopied instruction sheet that workers take to the construction site. It carries the specific orders from the DNA to the 'protein factories' in your cell. For example, mRNA vaccines work by giving your body a temporary 'instruction sheet' to learn how to recognize and fight a specific virus.",
    "photosynthesis": "Think of photosynthesis like a solar-powered kitchen inside a leaf. Plants take 'ingredients' like sunlight, water, and carbon dioxide, and 'cook' them into glucose (sugar) which is their food. A real-world example is how sunlight hitting a cornfield eventually turns into the energy you get when you eat a corn tortilla.",
    "osmosis": "Imagine a screen door that lets air through but keeps bugs out. Osmosis is like water trying to balance itself through a similar 'screen' (a membrane). A perfect real-time example is when you put a wilted stick of celery in a glass of water; the water 'osmosis' its way into the celery cells, making it crisp and firm again.",
    "diffusion": "Diffusion is like when someone opens a bottle of perfume in the corner of a room; slowly, the scent molecules spread out until you can smell it everywhere. In your body, this happens every second when oxygen moves from your lungs (where there's a lot of it) into your blood (where there's less of it) so your muscles can keep moving.",
    "catalyst": "Think of a catalyst like a GPS for a road trip. You could find your way without it, but it would take a lot more time and energy. The GPS doesn't drive the car, but it makes the journey much faster. In real life, the catalytic converter in your car speeds up the process of turning toxic exhaust into safer gases before they leave the tailpipe.",
    "catalysis": "Think of a catalyst like a GPS for a road trip. You could find your way without it, but it would take a lot more time and energy. The GPS doesn't drive the car, but it makes the journey much faster. In real life, the catalytic converter in your car speeds up the process of turning toxic exhaust into safer gases before they leave the tailpipe.",
    "organism": "An organism is like a complete, self-running city. Whether it's a tiny single-celled bacteria or a massive blue whale, it has its own systems for power (energy), waste removal, and building new structures (growth). For example, a single mushroom in a forest is a living organism that communicates with others through underground networks to survive.",
    "ecosystem": "Think of an ecosystem like a finely tuned orchestra where every instrumentâ€”from the tiny insects (violins) to the giant trees (cellos)â€”must play its part to keep the music going. If you remove the wolves from a forest, the deer overpopulate and eat all the plants, 'breaking' the music. A real-world example is a coral reef, where thousands of species rely on each other to survive in the ocean.",
    "gravity": "Gravity is like an invisible elastic band that connects everything in the universe. The bigger the object, the stronger the pull. Think of how the Earth's 'elastic band' keeps your feet firmly on the ground, while also reaching out into space to keep the Moon from drifting away, creating the ocean tides we see every day.",
}

LOCALIZATION = {
    "en": {
        "example_template": "Think of {term} as an essential gear in a clock. In the real world, biological researchers study this 'gear' to understand how the entire human body stays in sync, helping them invent new medicines that fix the clock when it breaks.",
        "chem_template": "Imagine {term} is like a secret ingredient in a recipe. In real-time industrial chemistry, using {term} correctly is the difference between a process that takes days and one that finishes in seconds, allowing us to create everything from batteries to clean drinking water faster and cheaper.",
        "phys_template": "Think of {term} like the invisible rules of a sport. Just as you can't play soccer without understanding how the ball bounces, engineers can't build safe rollercoasters or skyscrapers without calculating exactly how {term} will affect every beam and bolt.",
        "eco_template": "Imagine an ecosystem like a complex house of cards where {term} is one of the foundational cards. If environmental changes pull {term} out, the whole structure could wobble. Scientists study this to ensure our planet's 'house' stays standing for all living things.",
        "wiki_template": "To visualize {term}, think of it as a tool in a scientist's toolkit. Whether it's used to explain the stars or the cells in your skin, {term} provides a clear 'lens' that turns a confusing observation into a logical, understandable fact about our universe.",
        "fallback_template": "Think of {term} like a puzzle piece of the natural world. By understanding where this piece fits, we can see the 'big picture' of how science connects our daily livesâ€”like the food we eat or the air we breatheâ€”to the deep laws of nature.",
        "quiz_q1": "Based on the explanation, what is a primary characteristic of {term}?",
        "quiz_q2": "Which of these terms is directly related to the study of {term}?",
        "quiz_q3": "True or False: {term} plays a significant role in its respective scientific field.",
        "quiz_explanation_q1": "{term} is defined specifically by its role in the natural world as described.",
        "quiz_explanation_q2": "{concept} is a key component mentioned in the context of {term}.",
        "quiz_explanation_q3": "Scientific terms represent core concepts that are fundamental to understanding their fields.",
        "distractor_unrelated": "It is unrelated to {concept}",
        "distractor_vacuum": "It only applies in vacuum conditions",
        "distractor_year": "It was recently discovered in 2024",
        "distractor_marketing": "Digital marketing",
        "distractor_poetry": "Ancient poetry",
        "distractor_recipes": "Gordon Ramsay's recipes",
        "true": "True",
        "false": "False",
        "concept_theory": "Scientific theory",
        "concept_facts": "Observable facts",
        "concept_data": "Research data",
        "ui_real_life_example": "Real-Life Example",
        "ui_quick_quiz": "Quick Quiz",
        "ui_further_learning": "ðŸ“š Further Learning Resources",
        "ui_next": "Next Question â†’",
        "ui_finish": "Finish Quiz",
        "ui_correct": "Correct!",
        "ui_incorrect": "Incorrect",
        "ui_score_text": "Your Score",
        "ui_related_terms": "Related Concepts"
    },
    "hi": {
        "example_template": "{term} à¤•à¥‹ à¤ à¤• à¤˜à¤¡à¤¼à¥€ à¤®à¥‡à¤‚ à¤ à¤• à¤†à¤µà¤¶à¥ à¤¯à¤• à¤—à¤¿à¤¯à¤° à¤•à¥‡ à¤°à¥‚à¤ª à¤®à¥‡à¤‚ à¤¸à¥‹à¤šà¥‡à¤‚à¥¤ à¤µà¤¾à¤¸à¥ à¤¤à¤µà¤¿à¤• à¤¦à¥ à¤¨à¤¿à¤¯à¤¾ à¤®à¥‡à¤‚, à¤œà¥ˆà¤µà¤¿à¤• à¤¶à¥‹à¤§à¤•à¤°à¥ à¤¤à¤¾ à¤¯à¤¹ à¤¸à¤®à¤ à¤¨à¥‡ à¤•à¥‡ à¤²à¤¿à¤  à¤‡à¤¸ 'à¤—à¤¿à¤¯à¤°' à¤•à¤¾ à¤…à¤§à¥ à¤¯à¤¯à¤¨ à¤•à¤°à¤¤à¥‡ à¤¹à¥ˆà¤‚ à¤•à¤¿ à¤ªà¥‚à¤°à¤¾ à¤®à¤¾à¤¨à¤µ à¤¶à¤°à¥€à¤° à¤•à¥ˆà¤¸à¥‡ à¤¤à¤¾à¤²à¤®à¥‡à¤² à¤®à¥‡à¤‚ à¤°à¤¹à¤¤à¤¾ à¤¹à¥ˆ, à¤œà¤¿à¤¸à¤¸à¥‡ à¤‰à¤¨à¥ à¤¹à¥‡à¤‚ à¤¨à¤ˆ à¤¦à¤µà¤¾à¤ à¤‚ à¤¬à¤¨à¤¾à¤¨à¥‡ à¤®à¥‡à¤‚ à¤®à¤¦à¤¦ à¤®à¤¿à¤²à¤¤à¥€ à¤¹à¥ˆ à¤œà¥‹ à¤˜à¤¡à¤¼à¥€ à¤–à¤°à¤¾à¤ खराब होने पर उसे ठीक करती हैं।",
        "chem_template": "कल्पना कीजिए कि {term} एक नुस्खा में एक गुप्त घटक की तरह है। वास्तविक समय के औद्योगिक रसायन विज्ञान में, {term} का सही उपयोग उस प्रक्रिया के बीच का अंतर है जो दिनों लेती है और जो सेकंड में समाप्त होती है, जिससे हमें बैटरी से लेकर स्वच्छ पेयजल तक सब कुछ तेजी से और सस्ता बनाने की अनुमति मिलती है।",
        "phys_template": "{term} को किसी खेल के अदृश्य नियमों की तरह समझें। जिस तरह आप गेंद के उछलने के तरीके को समझे बिना फुटबॉल नहीं खेल सकते, इंजीनियर हर बीम और बोल्ट पर {term} के पड़ने वाले प्रभाव की गणना किए बिना सुरक्षित रोलरकोस्टर या गगनचुंबी इमारतें नहीं बना सकते।",
        "eco_template": "एक पारिस्थितिकी तंत्र की कल्पना ताश के पत्तों के एक जटिल घर की तरह करें जहां {term} मूलभूत पत्तों में से एक है। यदि पर्यावरणीय परिवर्तन {term} को बाहर निकाल देते हैं, तो पूरी संरचना लड़खड़ा सकती है। वैज्ञानिक यह सुनिश्चित करने के लिए इसका अध्ययन करते हैं कि हमारे ग्रह का 'घर' सभी जीवित चीजों के लिए खड़ा रहे।",
        "wiki_template": "{term} की कल्पना करने के लिए, इसे एक वैज्ञानिक के टूलकिट के एक उपकरण के रूप में सोचें। चाहे इसका उपयोग तारों या आपकी त्वचा की कोशिकाओं को समझाने के लिए किया जाए, {term} एक स्पष्ट 'लेंस' प्रदान करता है जो एक भ्रमित करने वाले अवलोकन को हमारे ब्रह्मांड के बारे में एक तार्किक, समझने योग्य तथ्य में बदल देता है।",
        "fallback_template": "{term} को प्राकृतिक दुनिया के एक पहेली के टुकड़े की तरह सोचें। यह समझकर कि यह टुकड़ा कहां फिट बैठता है, हम देख सकते हैं कि विज्ञान हमारे दैनिक जीवन को कैसे जोड़ता है—जैसे हम जो भोजन खाते हैं या जो हवा हम सांस लेते हैं—प्रकृति के गहरे नियमों से।",
        "quiz_q1": "स्पष्टीकरण के आधार पर, {term} की मुख्य विशेषता क्या है?",
        "quiz_q2": "इनमें से कौन सा शब्द {term} के अध्ययन से सीधे संबंधित है?",
        "quiz_q3": "सही या गलत: {term} अपने संबंधित वैज्ञानिक क्षेत्र में महत्वपूर्ण भूमिका निभाता है।",
        "quiz_explanation_q1": "{term} को विशेष रूप से वर्णित प्राकृतिक दुनिया में इसकी भूमिका द्वारा परिभाषित किया गया है।",
        "quiz_explanation_q2": "{concept} एक महत्वपूर्ण घटक है जिसका उल्लेख {term} के संदर्भ में किया गया है।",
        "quiz_explanation_q3": "वैज्ञानिक शब्द उन मूल अवधारणाओं का प्रतिनिधित्व करते हैं जो उनके क्षेत्रों को समझने के लिए मौलिक हैं।",
        "distractor_unrelated": "यह {concept} से संबंधित नहीं है",
        "distractor_vacuum": "यह केवल शून्य (वैक्यूम) स्थितियों में लागू होता है",
        "distractor_year": "इसे हाल ही में 2024 में खोजा गया था",
        "distractor_marketing": "डिजिटल मार्केटिंग",
        "distractor_poetry": "प्राचीन कविता",
        "distractor_recipes": "गॉर्डन रामसे के व्यंजन",
        "true": "सही",
        "false": "गलत",
        "concept_theory": "वैज्ञानिक सिद्धांत",
        "concept_facts": "अवलोकनीय तथ्य",
        "concept_data": "अनुसंधान डेटा",
        "ui_real_life_example": "वास्तविक जीवन का उदाहरण",
        "ui_quick_quiz": "त्वरित प्रश्नोत्तरी",
        "ui_further_learning": "ðŸ“š आगे सीखने के संसाधन",
        "ui_next": "अगला प्रश्न â†’",
        "ui_finish": "प्रश्नोत्तरी समाप्त करें",
        "ui_correct": "सही!",
        "ui_incorrect": "गलत",
        "ui_score_text": "आपका स्कोर",
        "ui_related_terms": "संबंधित अवधारणाएं"
    },
    "te": {
        "example_template": "{term} ని గడియారంలోని ఒక ముఖ్యమైన గేర్ లాగా భావించండి. నిజ ప్రపంచంలో, మానవ శరీరం ఎలా సమన్వయంతో ఉందో అర్థం చేసుకోవడానికి పరిశోధకులు దీనిని అధ్యయనం చేస్తారు.",
        "chem_template": "{term} ఒక రెసిపీలోని రహస్య పదార్థం వంటిదని ఊహించండి. పారిశ్రామిక రసాయన శాస్త్రంలో, {term} సరైన ఉపయోగం ప్రక్రియల వేగాన్ని పెంచుతుంది.",
        "phys_template": "{term} ని ఒక క్రీడ యొక్క అదృశ్య నియమాల లాగా అనుకోండి. {term} ప్రభావాన్ని లెక్కించకుండా ఇంజనీర్లు సురక్షితమైన నిర్మాణాలను నిర్మించలేరు.",
        "eco_template": "పర్యావరణ మార్పులు {term} ని తొలగిస్తే, మొత్తం పర్యావరణ వ్యవస్థ నిర్మాణం దెబ్బతింటుంది.",
        "wiki_template": "{term} ను శాస్త్రవేత్త యొక్క టూల్ కిట్ లోని ఒక పరికరంగా భావించండి. ఇది గందరగోళ పరిశీలనను అర్థమయ్యే వాస్తవంగా మారుస్తుంది.",
        "fallback_template": "{term} ని ప్రకృతి ప్రపంచంలోని ఒక పజిల్ ముక్కగా భావించండి. ఇది మన దైనందిన జీవితాన్ని ప్రకృతి నియమాలతో కలుపుతుంది.",
        "quiz_q1": "వివరణ ఆధారంగా, {term} యొక్క ప్రాథమిక లక్షణం ఏమిటి?",
        "quiz_q2": "వీటిలో ఏ పదం {term} అధ్యయనానికి నేరుగా సంబంధించి ఉంది?",
        "quiz_q3": "నిజమా లేదా అబద్ధమా: {term} తన శాస్త్రీయ రంగంలో ముఖ్యమైన పాత్ర పోషిస్తుంది.",
        "quiz_explanation_q1": "{term} వివరించిన విధంగా ప్రకృతి ప్రపంచంలో దాని పాత్ర ద్వారా ప్రత్యేకంగా నిర్వచించబడింది.",
        "quiz_explanation_q2": "{concept} అనేది {term} సందర్భంలో పేర్కొన్న కీలక అంశం.",
        "quiz_explanation_q3": "శాస్త్రీయ పదాలు వాటి రంగాలను అర్థం చేసుకోవడానికి ప్రాథమికమైనవి.",
        "distractor_unrelated": "దీనికి {concept} తో సంబంధం లేదు",
        "distractor_vacuum": "ఇది శూన్య పరిస్థితులలో మాత్రమే వర్తిస్తుంది",
        "distractor_year": "ఇది ఇటీవల 2024లో కనుగొనబడింది",
        "distractor_marketing": "డిజిటల్ మార్కెటింగ్",
        "distractor_poetry": "ప్రాచీన కవిత్వం",
        "distractor_recipes": "గోర్డాన్ రామ్సే వంటకాలు",
        "true": "నిజం",
        "false": "అబద్ధం",
        "concept_theory": "శాస్త్రీయ సిద్ధాంతం",
        "concept_facts": "గమనించదగ్గ వాస్తవాలు",
        "concept_data": "పరిశోధన డేటా",
        "ui_real_life_example": "నిజ జీవిత ఉదాహరణ",
        "ui_quick_quiz": "త్వరిత క్విజ్",
        "ui_further_learning": "ðŸ“š మరిన్ని అభ్యాస వనరులు",
        "ui_next": "తదుపరి ప్రశ్న â†’",
        "ui_finish": "క్విజ్ ముగించు",
        "ui_correct": "సరైనది!",
        "ui_incorrect": "తప్పు",
        "ui_score_text": "మీ స్కోర్",
        "ui_related_terms": "సంబంధిత అంశాలు"
    }
}

SCIENCE_GLOSSARY = {
    "dna": {
        "term": "DNA",
        "explanation": (
            "DNA (deoxyribonucleic acid) is the molecule that stores genetic instructions "
            "for growth, function, and reproduction in living organisms. It is built from "
            "four bases (A, T, C, G) arranged in a double-helix structure."
        ),
        "related_terms": ["Gene", "Chromosome"],
        "real_life_example": PREFERRED_EXAMPLES["dna"]
    },
    "rna": {
        "term": "RNA",
        "explanation": (
            "RNA (ribonucleic acid) helps convert genetic information into proteins. "
            "Unlike DNA, RNA is usually single-stranded and uses uracil (U) instead of thymine (T)."
        ),
        "related_terms": ["Protein synthesis", "mRNA"],
        "real_life_example": PREFERRED_EXAMPLES["rna"]
    },
    "photosynthesis": {
        "term": "Photosynthesis",
        "explanation": (
            "Photosynthesis is the process by which plants, algae, and some bacteria use sunlight "
            "to convert carbon dioxide and water into glucose and oxygen."
        ),
        "related_terms": ["Chlorophyll", "Glucose"],
        "real_life_example": PREFERRED_EXAMPLES["photosynthesis"]
    },
    "osmosis": {
        "term": "Osmosis",
        "explanation": (
            "Osmosis is the movement of water molecules through a semipermeable membrane "
            "from a region of lower solute concentration to higher solute concentration."
        ),
        "related_terms": ["Diffusion", "Semipermeable membrane"],
        "real_life_example": PREFERRED_EXAMPLES["osmosis"]
    },
    "diffusion": {
        "term": "Diffusion",
        "explanation": (
            "Diffusion is the net movement of particles from an area of higher concentration "
            "to an area of lower concentration due to random molecular motion."
        ),
        "related_terms": ["Concentration gradient", "Kinetic energy"],
        "real_life_example": PREFERRED_EXAMPLES["diffusion"]
    },
    "mitochondria": {
        "term": "Mitochondria",
        "explanation": (
            "Mitochondria are organelles in eukaryotic cells that produce ATP, the cell's main "
            "energy currency, through cellular respiration."
        ),
        "related_terms": ["ATP", "Cellular respiration"]
    },
    "gravity": {
        "term": "Gravity",
        "explanation": (
            "Gravity is the force of attraction between masses. Near Earth, it pulls objects "
            "toward the planet's center and gives them weight."
        ),
        "related_terms": ["Mass", "Weight"],
        "real_life_example": PREFERRED_EXAMPLES["gravity"]
    },
    "atom": {
        "term": "Atom",
        "explanation": (
            "An atom is the smallest unit of an element that retains its chemical properties. "
            "It consists of a nucleus (protons and neutrons) surrounded by electrons."
        ),
        "related_terms": ["Element", "Electron"]
    },
    "molecule": {
        "term": "Molecule",
        "explanation": (
            "A molecule is a group of two or more atoms chemically bonded together. "
            "Molecules can be made from the same element or different elements."
        ),
        "related_terms": ["Chemical bond", "Compound"]
    },
    "cell": {
        "term": "Cell",
        "explanation": (
            "A cell is the basic structural and functional unit of life. "
            "All living organisms are made of one or more cells."
        ),
        "related_terms": ["Organelle", "Tissue"]
    },
    "enzyme": {
        "term": "Enzyme",
        "explanation": (
            "An enzyme is a biological catalyst, usually a protein, that speeds up chemical reactions "
            "in living organisms without being consumed."
        ),
        "related_terms": ["Catalyst", "Active site"]
    },
    "ecosystem": {
        "term": "Ecosystem",
        "explanation": (
            "An ecosystem is a community of living organisms interacting with each other "
            "and with non-living components such as air, water, and soil."
        ),
        "related_terms": ["Biodiversity", "Food web"],
        "real_life_example": PREFERRED_EXAMPLES["ecosystem"]
    },
    "catalyst": {
        "term": "Catalyst",
        "explanation": (
            "A catalyst is a substance that increases the rate of a chemical reaction without being "
            "used up permanently in the process. It works by lowering the activation energy needed for "
            "reactants to form products, so reactions happen faster under the same conditions."
        ),
        "related_terms": ["Activation energy", "Reaction rate"],
        "real_life_example": PREFERRED_EXAMPLES["catalyst"]
    },
    "organism": {
        "term": "Organism",
        "explanation": (
            "An organism is any individual living thing, such as a bacterium, plant, fungus, or animal. "
            "Organisms carry out life processes including growth, reproduction, metabolism, and response "
            "to their environment."
        ),
        "related_terms": ["Cell", "Species"],
        "real_life_example": PREFERRED_EXAMPLES["organism"]
    },
}

STOPWORDS = {
    "about", "after", "again", "also", "among", "and", "another", "are", "because",
    "been", "being", "between", "both", "can", "cells", "concept", "each", "from",
    "have", "into", "its", "more", "most", "other", "over", "such", "that", "their",
    "them", "these", "this", "those", "through", "used", "using", "very", "when",
    "which", "with", "within", "without"
}


def _is_valid_related_term(candidate, term):
    if not candidate:
        return False

    text = candidate.strip()
    if not text:
        return False
    if ":" in text:
        return False
    if len(text) > 32:
        return False
    if re.search(r"\d", text):
        return False

    lowered = text.lower()
    lowered_term = (term or "").strip().lower()
    if lowered == lowered_term:
        return False

    banned = {"help", "template", "wikipedia", "article", "page"}
    if lowered in banned:
        return False

    return True


def _http_get_json(url):
    req = request.Request(
        url,
        headers={
            "User-Agent": "ConceptClarity/1.0 (educational app)",
            "Accept": "application/json"
        }
    )
    with request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _clean_text(text):
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned


def _first_sentences(text, max_sentences=6):
    cleaned = _clean_text(text)
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    selected = parts[:max_sentences]
    return " ".join(selected).strip()


def _extract_related_terms(term, text):
    lowered_term = (term or "").strip().lower()
    # Support more word characters to include scripts like Hindi/Telugu in extraction
    words = re.findall(r"\b\w{4,}\b", text or "")
    candidates = []
    seen = set()
    for raw in words:
        word = raw.strip()
        key = word.lower()
        if key == lowered_term or key in STOPWORDS:
            continue
        if key in seen:
            continue
        seen.add(key)
        candidates.append(word[0].upper() + word[1:] if len(word) > 1 else word)
        if len(candidates) == 3:
            break
    if len(candidates) < 2:
        return ["Scientific concept", "Real-world application"]
    return candidates


def _wikipedia_intro_links(title, term, language='en'):
    try:
        parse_url = (
            f"https://{language}.wikipedia.org/w/api.php"
            "?action=parse&prop=text&section=0&format=json"
            f"&page={parse.quote(title)}"
        )
        data = _http_get_json(parse_url)
        html = ((((data or {}).get("parse") or {}).get("text") or {}).get("*") or "")
        link_titles = re.findall(r'<a [^>]*title="([^"]+)"[^>]*>', html)

        results = []
        seen = set()
        for raw in link_titles:
            candidate = re.sub(r"\s*\(.*?\)\s*", "", raw).strip()
            key = candidate.lower()
            if not _is_valid_related_term(candidate, term):
                continue
            if key in seen:
                continue
            seen.add(key)
            results.append(candidate)
            if len(results) == 4:
                break
        return results if results else None
    except (error.URLError, TimeoutError, ValueError, KeyError):
        pass
    return None


def _refine_related_terms(term, candidate_terms, explanation, language='en'):
    preferred = PREFERRED_RELATED_TERMS.get((term or "").strip().lower())
    if preferred:
        return preferred

    cleaned = []
    seen = set()
    for item in (candidate_terms or []):
        candidate = re.sub(r"\s*\(.*?\)\s*", "", str(item)).strip()
        key = candidate.lower()
        if not _is_valid_related_term(candidate, term):
            continue
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(candidate)
        if len(cleaned) == 4:
            return cleaned

    fallback = _extract_related_terms(term, explanation)
    for item in fallback:
        key = item.lower()
        if key in seen:
            continue
        cleaned.append(item)
        seen.add(key)
        if len(cleaned) == 4:
            return cleaned

    while len(cleaned) < 2:
        cleaned.append(LOCALIZATION.get(language, LOCALIZATION['en']).get("concept_theory", "Concept"))
    return cleaned


def _real_life_example(term, explanation, source, language='en'):
    key = (term or "").strip().lower()
    if key in PREFERRED_EXAMPLES and language == 'en':
        return PREFERRED_EXAMPLES[key]

    loc = LOCALIZATION.get(language, LOCALIZATION['en'])
    text = (explanation or "").lower()

    if any(token in text for token in ["dna", "rna", "gene", "enzyme", "organism", "cell"]):
        return loc["example_template"].format(term=term)
    if any(token in text for token in ["reaction", "molecule", "atom", "chemical", "catalyst"]):
        return loc["chem_template"].format(term=term)
    if any(token in text for token in ["force", "energy", "gravity", "motion", "mass"]):
        return loc["phys_template"].format(term=term)
    if any(token in text for token in ["ecosystem", "species", "environment", "food web"]):
        return loc["eco_template"].format(term=term)

    if source == "wikipedia" or source == "wiktionary":
        return loc["wiki_template"].format(term=term)
    return loc["fallback_template"].format(term=term)


def _wikipedia_related_terms(title, term, extract_text, language='en'):
    intro_links = _wikipedia_intro_links(title, term, language)
    if intro_links:
        refined = _refine_related_terms(term, intro_links, extract_text, language)
        if len(refined) >= 2:
            return refined

    try:
        links_url = (
            f"https://{language}.wikipedia.org/w/api.php"
            "?action=query&prop=links&pllimit=max&format=json&redirects=1"
            f"&titles={parse.quote(title)}"
        )
        data = _http_get_json(links_url)
        pages = (((data or {}).get("query") or {}).get("pages") or {})
        page = next(iter(pages.values()), {})
        links = page.get("links") or []

        results = []
        seen = set()
        for item in links:
            name = (item or {}).get("title", "").strip()
            key = name.lower()
            if not _is_valid_related_term(name, term):
                continue
            if key in seen:
                continue
            seen.add(key)
            results.append(name)
            if len(results) == 5:
                break

        if len(results) >= 2:
            return _refine_related_terms(term, results, extract_text, language)
    except (error.URLError, TimeoutError, ValueError, KeyError):
        pass

    return _refine_related_terms(term, [], extract_text, language)


def _wikipedia_explanation(term, language='en'):
    encoded = parse.quote((term or "").strip())
    if not encoded:
        return None

    try:
        search_url = (
            f"https://{language}.wikipedia.org/w/api.php"
            f"?action=query&list=search&srsearch={encoded}&format=json&srlimit=1"
        )
        search_data = _http_get_json(search_url)
        hits = (((search_data or {}).get("query") or {}).get("search") or [])
        title = hits[0].get("title") if hits else term

        extract_url = (
            f"https://{language}.wikipedia.org/w/api.php"
            "?action=query&prop=extracts&explaintext=1&redirects=1&format=json"
            f"&titles={parse.quote(title)}"
        )
        page_data = _http_get_json(extract_url)
        pages = (((page_data or {}).get("query") or {}).get("pages") or {})
        page = next(iter(pages.values()), {})
        extract = _first_sentences(page.get("extract"), max_sentences=12)
        if not extract:
            return None
        return {
            "term": title,
            "explanation": extract,
            "related_terms": _wikipedia_related_terms(title, term, extract, language),
            "real_life_example": _real_life_example(title, extract, "wikipedia", language),
            "source": "wikipedia"
        }
    except (error.URLError, TimeoutError, ValueError, KeyError):
        return None


def _wiktionary_explanation(term, language='en'):
    encoded = parse.quote((term or "").strip())
    if not encoded:
        return None

    try:
        url = (
            f"https://{language}.wiktionary.org/w/api.php"
            "?action=query&prop=extracts&explaintext=1&exintro=1&redirects=1&format=json"
            f"&titles={encoded}"
        )
        data = _http_get_json(url)
        pages = (((data or {}).get("query") or {}).get("pages") or {})
        page = next(iter(pages.values()), {})
        extract = _first_sentences(page.get("extract"), max_sentences=8)
        if not extract:
            return None
        readable_term = page.get("title") or term
        return {
            "term": readable_term,
            "explanation": extract,
            "related_terms": _refine_related_terms(readable_term, [], extract, language),
            "real_life_example": _real_life_example(readable_term, extract, "wiktionary", language),
            "source": "wiktionary"
        }
    except (error.URLError, TimeoutError, ValueError, KeyError):
        return None


def _load_model_once():
    global tokenizer, model, model_error
    if tokenizer is not None and model is not None:
        return True
    if model_error is not None:
        return False
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name, local_files_only=True)
        return True
    except Exception as exc:
        model_error = str(exc)
        return False


def _fallback_explanation(term, language='en'):
    cleaned = (term or "").strip()
    readable = cleaned if cleaned else "Unknown term"
    loc = LOCALIZATION.get(language, LOCALIZATION['en'])
    explanation = (
        f"{readable} is a scientific concept. It describes an idea, object, process, or living system "
        "used to explain how the natural world works."
    )
    return {
        "term": readable,
        "explanation": explanation,
        "related_terms": ["Observation", "Hypothesis"],
        "real_life_example": _real_life_example(readable, explanation, "fallback", language),
        "source": "fallback"
    }


def _glossary_explanation(term, language='en'):
    key = (term or "").strip().lower()
    hit = SCIENCE_GLOSSARY.get(key)
    if not hit:
        return None
    enriched = dict(hit)
    if not enriched.get("real_life_example"):
        enriched["real_life_example"] = _real_life_example(enriched.get("term", term), enriched.get("explanation", ""), "glossary", language)
    enriched["source"] = "glossary"
    return enriched


def _extract_json_object(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _normalize_response(term, payload, language='en'):
    if not isinstance(payload, dict):
        return _fallback_explanation(term, language)
    normalized = {
        "term": payload.get("term") or term,
        "explanation": payload.get("explanation") or _fallback_explanation(term, language)["explanation"],
        "related_terms": _refine_related_terms(
            payload.get("term") or term,
            payload.get("related_terms") or [],
            payload.get("explanation") or "",
            language
        ),
        "real_life_example": payload.get("real_life_example") or _real_life_example(
            payload.get("term") or term,
            payload.get("explanation") or "",
            payload.get("source") or "model",
            language
        ),
        "source": payload.get("source") or "model"
    }
    return normalized


def _generate_quiz(term, explanation, language='en'):
    if not explanation:
        return None
    
    loc = LOCALIZATION.get(language, LOCALIZATION['en'])
    
    # Extract thematic concepts from explanation
    words = re.findall(r"\b\w{5,}\b", explanation)
    concepts = [w for w in words if w.lower() not in STOPWORDS and w.lower() != term.lower()]
    concepts = list(dict.fromkeys(concepts)) # unique
    
    # Thematic distractor pools
    thematic_pools = {
        "biology": ["Mitochondria", "Homeostasis", "Metabolism", "DNA", "RNA", "Cell", "Gene", "Species"],
        "physics": ["Kinetic energy", "Quantum", "Thermodynamics", "Force", "Mass", "Velocity", "Gravity", "Atom"],
        "chemistry": ["Catalysis", "Molecule", "Stoichiometry", "Bond", "Oxidation", "pH", "Reaction", "Element"]
    }
    
    # Detect theme
    exp_lower = explanation.lower()
    if any(k in exp_lower for k in ["cell", "dna", "plant", "organism", "bio"]):
        pool = thematic_pools["biology"]
    elif any(k in exp_lower for k in ["force", "energy", "phys", "motion"]):
        pool = thematic_pools["physics"]
    else:
        pool = thematic_pools["chemistry"]
    
    final_concepts = concepts + [c for c in pool if c.lower() not in [w.lower() for w in concepts] and c.lower() != term.lower()]
    
    if len(final_concepts) < 8:
        final_concepts += ["System", "Mechanism", "Process", "Data", "Observation"]
    
    answers = final_concepts[:3]
    pool_for_dists = final_concepts[3:]
    
    questions = []
    q_titles = ["quiz_q1", "quiz_q2", "quiz_q3"]
    
    for i in range(3):
        ans = answers[i]
        dists = random.sample(pool_for_dists, 3)
        options = [ans] + dists
        random.shuffle(options)
        
        questions.append({
            "question": loc.get(q_titles[i], "What is related to {term}?").format(term=term),
            "options": options,
            "answer": ans,
            "explanation": loc.get(f"quiz_explanation_q{i+1}", "This is correct based on the explanation.").format(term=term, concept=ans),
            "related_concepts": random.sample(pool_for_dists, 2)
        })
        
    return {
        "questions": questions,
        "advanced_analytics": {
            "difficulty": "Academic/Expert",
            "suggested_reading": [f"Deep dive into {answers[0]}", f"Applications of {term}"]
        }
    }


def generate_explanation(term, language='en'):
    wiki_hit = _wikipedia_explanation(term, language)
    if wiki_hit:
        wiki_hit["quiz"] = _generate_quiz(wiki_hit["term"], wiki_hit["explanation"], language)
        return wiki_hit

    wiktionary_hit = _wiktionary_explanation(term, language)
    if wiktionary_hit:
        wiktionary_hit["quiz"] = _generate_quiz(wiktionary_hit["term"], wiktionary_hit["explanation"], language)
        return wiktionary_hit

    glossary_hit = _glossary_explanation(term, language)
    if glossary_hit:
        glossary_hit["quiz"] = _generate_quiz(glossary_hit["term"], glossary_hit["explanation"], language)
        return glossary_hit

    prompt = build_prompt(term, language)
    if not _load_model_once():
        fallback = _fallback_explanation(term, language)
        fallback["quiz"] = _generate_quiz(fallback["term"], fallback["explanation"], language)
        return fallback

    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
        outputs = model.generate(**inputs, max_length=520, temperature=0.4, do_sample=True)
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        parsed = _extract_json_object(response_text)
        response = _normalize_response(term, parsed, language)
        if "quiz" not in response or not response["quiz"] or "questions" not in response["quiz"]:
            response["quiz"] = _generate_quiz(response["term"], response["explanation"], language)
        return response
    except Exception:
        fallback = _fallback_explanation(term, language)
        fallback["quiz"] = _generate_quiz(fallback["term"], fallback["explanation"], language)
        return fallback