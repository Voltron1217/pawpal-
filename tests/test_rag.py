import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Owner, Pet, Scheduler, Task
from rag import Retriever, answer, build_prompt, load_chunks, schedule_context


def test_knowledge_base_loads_one_chunk_per_section():
    chunks = load_chunks()
    assert len(chunks) >= 10
    assert all(c.title and c.text for c in chunks)


def test_retrieval_finds_the_right_section():
    top = Retriever().search("how often should I walk my dog")[0][0]
    assert top.title == "Dog walking and exercise"


def test_retrieval_separates_cats_from_dogs():
    top = Retriever().search("how often do I scoop the cat litter box")[0][0]
    assert top.title == "Cat litter box care"


def test_irrelevant_or_empty_question_retrieves_nothing():
    retriever = Retriever()
    assert retriever.search("") == []
    assert retriever.search("quantum chromodynamics lagrangian") == []


def test_prompt_contains_retrieved_text_and_schedule():
    owner = Owner("Alice")
    pet = Pet("Spot", 5, "Beagle")
    owner.add_pet(pet)
    pet.add_task(Task("Evening walk", datetime(2024, 6, 3, 18, 0), "daily"))
    sched = Scheduler(owner)
    hits = Retriever().search("walk my dog")

    prompt = build_prompt("How long should walks be?", hits, schedule_context(sched, pet))

    assert "Dog walking and exercise" in prompt and "Evening walk" in prompt and "Beagle" in prompt


def test_answer_without_api_key_falls_back_to_retrieved_passages(monkeypatch):
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    owner = Owner("Alice")
    pet = Pet("Spot", 5, "Beagle")
    owner.add_pet(pet)

    text, sources, used_llm = answer("how often should I walk my dog", Scheduler(owner), pet)

    assert used_llm is False and sources and "walk" in text.lower()


# --- more species ------------------------------------------------------------
import pytest

from breeds import BREEDS, MIXED
from rag import SPECIES_FILES


def test_every_species_has_breeds_and_a_guide():
    assert len(BREEDS) == 7 and {"Rabbit", "Bird", "Hamster", "Guinea Pig", "Turtle"} <= set(BREEDS)
    sources = {c.source for c in load_chunks()}
    for species, breeds in BREEDS.items():
        assert breeds and MIXED not in breeds
        assert SPECIES_FILES[species] <= sources, species


@pytest.mark.parametrize(
    "species,question,expected_title",
    [
        ("Rabbit", "How long should my rabbit be out of its cage each day?", "Rabbit exercise and play"),
        ("Bird", "How often should I clean my bird's cage?", "Bird cage cleaning"),
        ("Guinea Pig", "Why does my guinea pig need vitamin C?", "Guinea pig feeding"),
        ("Turtle", "How long should my turtle's UVB light be on?", "Turtle lighting and habitat"),
        ("Turtle", "How often should I feed my turtle?", "Turtle feeding"),
    ],
)
def test_new_species_questions_find_their_own_guide(species, question, expected_title):
    hits = Retriever().search(question, sources=SPECIES_FILES[species] | {"general.md"})
    assert hits[0][0].title == expected_title


def test_a_rabbit_never_gets_dog_or_cat_advice(monkeypatch):
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    owner = Owner("Alice")
    bunny = Pet("Thumper", 2, "Holland Lop", species="Rabbit")
    owner.add_pet(bunny)

    _, sources, _ = answer("how often should I feed and brush my pet", Scheduler(owner), bunny)

    assert sources and all(s.startswith(("rabbits.md", "breeds/rabbits.md", "general.md")) for s in sources)


def test_bunny_is_treated_as_rabbit():
    top = Retriever().search("how much hay does my bunny need")[0][0]
    assert top.source == "rabbits.md"
