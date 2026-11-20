import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import MAX_OWNER_NAME, OwnerDirectory, Pet

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


# --- OwnerDirectory ------------------------------------------------------------
def test_owners_keep_separate_pets_even_with_the_same_pet_name():
    directory = OwnerDirectory()
    alice, bob = directory.add("Alice"), directory.add("Bob")
    alice.add_pet(Pet("Spot", 3, "Beagle"))
    bob.add_pet(Pet("Spot", 5, "Pug"))  # same name, different owner: allowed
    assert [p.breed for p in alice.pets] == ["Beagle"] and [p.breed for p in bob.pets] == ["Pug"]


def test_same_pet_name_twice_for_one_owner_is_still_rejected():
    owner = OwnerDirectory().add("Alice")
    owner.add_pet(Pet("Spot", 3, "Beagle"))
    with pytest.raises(ValueError):
        owner.add_pet(Pet("Spot", 1, "Pug"))


@pytest.mark.parametrize("bad", ["", "   ", None, "x" * (MAX_OWNER_NAME + 1)])
def test_blank_or_overlong_owner_names_are_rejected(bad):
    with pytest.raises(ValueError):
        OwnerDirectory().add(bad)


def test_duplicate_owner_names_are_rejected_ignoring_case_and_spaces():
    directory = OwnerDirectory()
    directory.add("Alice")
    for dup in ("alice", "  ALICE ", "Alice"):
        with pytest.raises(ValueError):
            directory.add(dup)
    assert directory.names() == ["Alice"] and len(directory) == 1


def test_lookup_and_order():
    directory = OwnerDirectory()
    directory.add("Zoe")
    directory.add("Alice")
    assert directory.names() == ["Zoe", "Alice"] and "Zoe" in directory and "Nobody" not in directory
    assert directory.get("Alice").name == "Alice" and directory.get("Nobody") is None and directory.get(None) is None


# --- the app ---------------------------------------------------------------------
def _at():
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(APP, default_timeout=60).run()


def _add_owner(at, name):
    [t for t in at.text_input if t.label == "Owner name"][0].set_value(name)
    [b for b in at.button if b.label == "Add owner"][0].click().run()


def _add_pet(at, name, species="Dog", breed="Beagle"):
    at.radio[0].set_value(species).run()
    [t for t in at.text_input if t.label == "Pet name"][0].set_value(name)
    [s for s in at.selectbox if "breed" in s.label][0].select(breed)
    [b for b in at.button if b.label == "Add pet"][0].click().run()


def test_app_asks_for_an_owner_first():
    at = _at()
    assert not at.exception and any("Add an owner" in i.value for i in at.info)
    assert not [b for b in at.button if b.label == "Add pet"]  # nothing else is shown yet


def test_two_owners_can_each_have_a_pet_with_the_same_name():
    at = _at()
    _add_owner(at, "Alice")
    _add_pet(at, "Spot", breed="Beagle")
    assert not at.error

    _add_owner(at, "Bob")  # the new owner is selected automatically
    assert at.session_state.current_owner == "Bob"
    _add_pet(at, "Spot", breed="Pug")  # used to fail with "Spot already exists"
    assert not at.error and not at.exception

    directory = at.session_state.directory
    assert [p.breed for p in directory.get("Alice").pets] == ["Beagle"]
    assert [p.breed for p in directory.get("Bob").pets] == ["Pug"]


def test_switching_owner_shows_only_that_owners_pets():
    at = _at()
    _add_owner(at, "Alice")
    _add_pet(at, "Spot")
    _add_owner(at, "Bob")
    _add_pet(at, "Rex", breed="Pug")

    [s for s in at.selectbox if s.label == "Who is using PawPal+?"][0].select("Alice").run()
    text = " ".join(w.value for w in at.markdown)
    assert "Alice's pets: Spot" in text and "Rex" not in text and not at.exception


def test_same_pet_name_for_the_same_owner_is_still_an_error():
    at = _at()
    _add_owner(at, "Alice")
    _add_pet(at, "Spot")
    _add_pet(at, "Spot")
    assert any("already exists" in e.value for e in at.error)


def test_duplicate_owner_name_shows_a_friendly_error():
    at = _at()
    _add_owner(at, "Alice")
    _add_owner(at, "alice")
    assert any("Could not add owner" in e.value for e in at.error) and len(at.session_state.directory) == 1
