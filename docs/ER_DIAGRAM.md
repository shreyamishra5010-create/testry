# Data model (MongoDB collections)

Each entity is a collection whose `_id` is an integer from the `counters` collection (`{_id: <collection>, seq}`). The API exposes it as `id`. Relationships are id references, and the app enforces cascades.

```mermaid
erDiagram
    USERS ||--o{ BOARDS : owns
    USERS ||--o{ BOARD_MEMBERS : "belongs to"
    BOARDS ||--o{ BOARD_MEMBERS : has
    BOARDS ||--o{ COLUMNS : contains
    BOARDS ||--o{ TASKS : contains
    COLUMNS ||--o{ TASKS : holds
    USERS |o--o{ TASKS : "assigned to"
    USERS ||--o{ TASKS : creates
    TASKS ||--o{ COMMENTS : has
    USERS ||--o{ COMMENTS : writes
    BOARDS ||--o{ ACTIVITY : logs
    USERS |o--o{ ACTIVITY : performs

    USERS {
        int id PK
        text name
        text email UK
        text password_hash
        text created_at
    }
    BOARDS {
        int id PK
        text name
        text description
        int owner_id FK
        text created_at
    }
    BOARD_MEMBERS {
        int board_id PK,FK
        int user_id PK,FK
        text role "owner | member"
    }
    COLUMNS {
        int id PK
        int board_id FK
        text name
        int position
        text color
    }
    TASKS {
        int id PK
        int board_id FK
        int column_id FK
        text title
        text description
        text priority "low | medium | high"
        text due_date
        int assignee_id FK "nullable"
        int position
        int created_by FK
        text created_at
        text updated_at
    }
    COMMENTS {
        int id PK
        int task_id FK
        int user_id FK
        text body
        text created_at
    }
    ACTIVITY {
        int id PK
        int board_id FK
        int user_id FK "nullable"
        text action
        text message
        text created_at
    }
```

## Cascade rules
| Delete | Effect |
|---|---|
| Board | Its members, columns, tasks, comments, and activity are deleted |
| Column | Its tasks and their comments are deleted |
| Task | Its comments are deleted |
| User | Assigned tasks become unassigned (`SET NULL`) |
| Member removed from board | Their assignments on that board are cleared |
