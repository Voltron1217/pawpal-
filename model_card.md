# PawPal+ Model Card

PawPal+ is a Streamlit pet-care scheduler with an "Ask PawPal" assistant. The assistant is a RAG pipeline ([rag.py](rag.py)). It retrieves passages from a small hand-written knowledge base (`knowledge/*.md`, plus per-breed guides) using TF-IDF. It adds the pet's own records and schedule, then asks Gemini (or Claude) to answer using only that material. A second feature ([actions.py](actions.py)) turns requests like "add a 6pm walk for Casper every day" into a *proposed* task. The owner has to confirm it before it is added.

## 1. Limitations and biases

**Limited knowledge, not a vet.**
- The answers are only as good as the markdown files I wrote. They cover seven species (dog, cat, rabbit, bird, hamster, guinea pig, turtle).
- Anything outside those species, such as a ferret, snake or horse, finds no passages and gets "ask your vet".
- The guides are general. They are not a diagnosis, and the system has no way to tell an emergency from a routine question. A user describing a poisoning gets the same calm, brief answer as a user asking about nail trimming.

**Popularity bias.**
- Dogs and cats get the deepest coverage, including per-breed guides. Birds, small mammals and turtles get thinner coverage, so owners of less common pets get less specific advice.
- Breed guides only exist for breeds I listed. Mixed or rare breeds fall back to general species advice.

**Keyword retrieval, not meaning.**
- TF-IDF with a crude stemmer (strip a plural "s" or "ing") and a hand-made alias table (`puppy -> dog`, `meds -> medication`) matches words, not intent.
- A question phrased with vocabulary I didn't anticipate can retrieve nothing, or the wrong section, even though the right answer is in the files. `min_score=0.12` is a threshold I tuned by hand on a few examples.
- The prompt still tells the model to say when the material doesn't cover the question, but the model can paraphrase a retrieved passage a little too confidently.

**English and US-centric assumptions.**
- Questions are parsed and answered in English only.
- Times are written like "6pm" or "18:00". Weights have no unit handling, so `Weight: 12` could be kilos or pounds.
- Care advice reflects common US/Western guidance, such as vaccine schedules and "senior at 10 years".

**Heuristic input parsing.**
- The offline task parser is regex-based. It handles common phrasings, not every way a person talks.
- When the LLM is unavailable, free-form requests may be misread or rejected. Everything is validated by the same checks as the manual form, and nothing is added without a confirm click.

**Depends on an outside model.** Answer wording and quality depend on Gemini or Claude and can change when the model version changes. The offline fallback is only the raw retrieved text, which is accurate to my files but not conversational.

## 2. Could the AI be misused, and how is that prevented?

**Realistic misuse risks**
1. *Prompt injection.* A user asks the assistant to ignore its rules or reveal the API key. A subtler version hides instructions in the pet's free-text notes, diet or medication fields, which are pasted into the prompt.
2. *Treated as medical advice.* An owner might skip the vet because "PawPal said it was fine", for example with medication doses or a sick animal.
3. *Cost or abuse of the API key.* Very long inputs, or repeated calls, could burn quota.
4. *Leaking secrets through logs or errors.* API errors can echo the key.
5. *Unwanted actions.* A crafted message could trick the assistant into silently changing the schedule.

**What is in place**
- **Input cleaning:** `clean_question` strips control characters, collapses whitespace and caps questions at 300 characters. Owner-written record text is cleaned and capped at 300 characters per line too (`_record_text`).
- **Injection filter:** questions that match patterns like "ignore previous instructions", "system prompt" or "api key" are refused before any model call. Pet-record lines that match are dropped, with a warning logged. The prompt also says the records are data and never instructions.
- **Grounding:** the model is told to answer only from the supplied material and to say so if the material doesn't cover the question. When guidance conflicts with a pet's allergies or medications, it must follow the records and tell the owner to check with their vet.
- **Species filtering:** a rabbit's question only searches rabbit and general files, so it can't receive dog advice that could be harmful.
- **Human-in-the-loop for actions:** `actions.interpret()` never changes the schedule. It only returns a proposal, and the owner presses Confirm.
- **Failure handling:** `answer()` never raises. Model errors, empty replies and retrieval crashes all fall back to a safe message or to the retrieved passages. Answers are capped at 2000 characters.
- **Secret hygiene:** `redact()` strips keys from anything logged, and `pawpal.log*` and `secrets.toml` are git-ignored.

**What is not solved**
- A regex blocklist is easy to get around with rewording, so the injection filter is a speed bump and not a wall. The stronger defences are the grounding instructions and the confirm step.
- There is no rate limiting and no emergency detection.
- The app shows sources, but it does not yet show a persistent "not a substitute for a vet" banner on every answer. That would be the next addition.

## 3. What surprised me while testing reliability

I ran 187 automated tests (all passing). Most of the surprises came from writing them and from the retrieval logging, not from the happy path.

- **Retrieval, not the LLM, was the fragile part.** I expected the model to be the unreliable piece. Instead, most wrong answers came from the wrong passage being retrieved. Adding the species word to the query *skewed* the ranking once results were already filtered by species, so I now only add it when unfiltered (see the comment in `answer()`).
- **Tiny vocabulary gaps broke retrieval.** "Puppy", "meds" and "bunny" retrieved nothing until I added aliases. Plurals and "-ing" forms (walks/walking) needed the stemmer. A real user's wording is much more varied than mine.
- **Cross-species leakage was real.** Before species filtering, a rabbit question could surface dog or cat sections, because words like "feeding" and "vet" overlap. I added a test (`test_a_rabbit_never_gets_dog_or_cat_advice`) to keep it fixed.
- **The model sometimes returned empty or very long replies**, and API failures could carry the key in the error text. I hadn't planned for either until I wrote the guardrail tests. They are why `answer()` falls back to retrieved text, truncates, and logs through `redact()`.
- **The offline fallback was better than I expected.** With no API key, returning the retrieved passages directly is often a perfectly good answer. It made me realise how much of the value is in retrieval and grounding and how little is in the generation.
- **User data is also an attack surface.** I had focused on the question box, but the pet's notes and medication fields reach the prompt too. That is why records are sanitised and screened.

## 4. Collaboration with AI

I used AI (Claude Code and Gemini inside the app) as a pair programmer: to draft modules, suggest test cases and review edge cases. I made the design decisions and checked the output by running the test suite.

> **Note for review:** I wrote the examples below from what the code and its comments show. Before submitting, confirm they match what you remember from the sessions, and adjust the wording if not.

### A suggestion I accepted: propose first, then confirm
For "add a 6pm walk for Casper every day", the AI suggested that the assistant should not write to the schedule directly. It should return a proposal that the owner approves, which is how `actions.interpret()` works. I accepted this because it fit my goal: owners who are busy and worried should not find surprise tasks on their schedule. It also handles misparsed times and gives prompt injection no route to change data. The result is simple to test (a proposal is a plain object). It also let me reuse the same `Task` validation as the Add-task form.

### A suggestion I did not accept as written: heavier retrieval
A common suggestion for RAG is to use embeddings and a vector database (or a library such as scikit-learn or LangChain) for retrieval. I kept a small pure-Python TF-IDF retriever in [rag.py](rag.py). For a knowledge base of a few dozen short hand-written sections, a vector store was over-engineered. It would add dependencies, make the app harder to install, and break the offline fallback. It would also make the ranking harder to explain and debug. TF-IDF let me print each retrieved section and its score in the log and fix problems directly (aliases, title weighting, species filters). The trade-off is the keyword-matching limitation described in section 1. If the knowledge base grows a lot, embeddings would be worth revisiting.

### Other places I changed AI output
- **Scoped down the injection filter:** a broader keyword list kept blocking harmless pet questions, so I narrowed it to specific phrases. This is also why the filter is only a first layer.
- **Added fallbacks the AI's first draft did not have:** the first draft of the answer function assumed the model call would succeed. I added the offline fallback, truncation and `redact()` logging after testing failures.

### What I learned about working with AI
It is fast at producing working code and test scaffolding, and it was useful for thinking of failure cases. It tends toward the "standard" heavy solution and toward assuming the happy path. The most valuable thing I did was run the tests and the real app after each change, and ask whether each addition actually fit a small project.
