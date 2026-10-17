from dataclasses import dataclass, field


@dataclass
class Owner:
    name: str
    owner_id: int
    phone: str

    def add_owner(self) -> None:
        pass


@dataclass
class Pet:
    name: str
    age: int
    breed: str
    pet_id: int

    def add_pet(self) -> None:
        pass


@dataclass
class Scheduling:
    appointment_date: str
    appointment_id: int
    pet_id: int
    payments: int
    task: str

    def schedule_appointment(self) -> None:
        pass


@dataclass
class Task:
    pet_id: int
    task: str
    appointment_id: int
    weight_of_dog: int
    notes_ask_question_to_owner: str
    medicine: dict = field(default_factory=dict)

    def add_task(self) -> None:
        pass
