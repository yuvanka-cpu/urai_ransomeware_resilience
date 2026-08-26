# URAI Ransomware Resilience — Repository Map

## Purpose

This repository contains a synthetic, defensive Proof of Concept for
Energy & Petrochemical Ransomware Resilience.

The Stage 0 implementation focuses on backend foundation, API contracts,
safe mocked responses, validation, and testing.

## Current Structure

```text
urai_ransomeware_resilience/
├── apps/
│   └── backend/
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── audit/
│       │   ├── controllers/
│       │   ├── policies/
│       │   ├── routes/
│       │   ├── services/
│       │   │   └── ransomware_mock.py
│       │   └── schemas/
│       │       ├── enums.py
│       │       ├── requests.py
│       │       └── responses.py
│       ├── tests/
│       │   ├── test_api.py
│       │   ├── test_health.py
│       │   └── test_schemas.py
│       └── pytest.ini
├── docs/
│   └── ransomware/
│       └── repository_map.md
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```