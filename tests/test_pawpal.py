from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    task = Task(name="Morning Walk", task_type="exercise", duration=30, priority="high")
    assert task.is_complete is False
    task.mark_complete()
    assert task.is_complete is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Mochi", age=3, breed="Shiba Inu", weight=20.5)
    assert len(pet.tasks) == 0
    task = Task(name="Feeding", task_type="nutrition", duration=10, priority="high", target_pet=pet)
    pet.tasks.append(task)
    assert len(pet.tasks) == 1
