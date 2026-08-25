from . import phase1, phase2, phase3, phase4, phase5

ALL_TASKS = (phase1.TASKS + phase2.TASKS + phase3.TASKS
             + phase4.TASKS + phase5.TASKS)
BY_ID = {t.id: t for t in ALL_TASKS}
