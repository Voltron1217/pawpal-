# PawPal+ Project Reflection

## 1. System Design



**a. Initial design**

- Briefly describe your initial UML design.
So i was thinking about creating three things which are adding pets, scheduling, and todo list. 
1. add a pet.
    1. name of the pet: string
    2. age: int 
    3. breed: string
    4. petId: int
2. scheduling:
    1. appointment date: string
    2. appointmentID: int
    3. petId: int
    4. payments: int
    5. Task: string
3. todo:
    1. petId: int
    2. Task: string
    3. appointmentId: int
    4. weight_of_dog: int
    5. notes_ask_question_to_the_owner: string
    6. medicine: dict
```mermaid
classDiagram
    class Owner {
        +String name
        +int ownerId
        +String phone
        +addOwner() void
    }

    class Pet {
        +String name
        +int age
        +String breed
        +int petId
        +addPet() void
    }

    class Scheduling {
        +String appointmentDate
        +int appointmentId
        +int petId
        +int payments
        +String task
        +scheduleAppointment() void
    }

    class Todo {
        +int petId
        +String task
        +int appointmentId
        +int weightOfDog
        +String notesAskQuestionToOwner
        +dict medicine
        +addTask() void
    }

    Owner "1" --> "1..*" Pet : owns
    Pet "1" --> "0..*" Scheduling : has appointments
    Pet "1" --> "0..*" Todo : has tasks
    Scheduling "1" --> "0..*" Todo : includes
```

- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
