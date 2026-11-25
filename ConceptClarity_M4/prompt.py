def build_prompt(term, language='en'):
    return f"""
You are an Elite Academic Researcher and Senior Scientific Educator. Your mission is to decompose complex concepts into profound, high-level structural insights.

TASK: Provide an expert-level, comprehensive explanation of '{term}' in {language}. 

TARGET AUDIENCE: Post-graduate level / Subject matter enthusiasts. Use rigorous scientific terminology but maintain conceptual clarity.

REQUIRED STRUCTURE:
1.  **Etymology & Axiomatic Definition**: Trace the linguistic roots and provide a mathematically/scientifically rigorous definition.
2.  **Fundamental Mechanisms**: Deep-dive into the underlying physical, chemical, or biological processes. Explain 'why' and 'how' at the molecular/atomic/quantum level.
3.  **Heuristic Analogy**: An advanced, elegant analogy that captures the systemic behavior of the concept.
4.  **Functional Significance**: Why is this indispensable to its field and the broader scientific paradigm?
5.  **Interdisciplinary Convergence**: How does this concept bridge multiple domains (e.g., Entropy in Thermodynamics vs. Information Theory)?
6.  **Empirical Case Study**: A high-fidelity, real-world application or modern research example involving {term}.

QUIZ (Cognitive Challenge Level):
Generate 3 highly conceptual multiple-choice questions that test deep understanding rather than rote memorization.
- Focus on emergent properties, limit cases, and counter-intuitive results.
- Provide 4 sophisticated options that reveal common misconceptions.
- Include 'Contextual Nuance' notes for the answer explanation.

CRITICAL: Return ONLY valid JSON. Every text field—including keys when possible, but definitely all values—MUST be in {language}.

JSON SCHEMA:
{{
  "term": "{term}",
  "explanation": "...",
  "related_terms": ["...", "...", "...", "..."],
  "real_life_example": "...",
  "quiz": {{
    "questions": [
      {{
        "question": "...",
        "options": ["...", "...", "...", "..."],
        "answer": "...",
        "explanation": "...",
        "related_concepts": ["...", "..."]
      }}
    ],
    "advanced_analytics": {{
       "difficulty": "Academic/Expert",
       "suggested_reading": ["...", "..."]
    }}
  }}
}}

Term: {term}
Language: {language}
"""