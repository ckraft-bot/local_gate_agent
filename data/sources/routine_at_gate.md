# Gate Agent Routine at the Gate

## Key Responsibilities

- Review flight details, operational updates, boarding rules, and passenger-service requirements before opening the gate.
- Check in the operating crew and coordinate with the flight crew, ramp team, and operations control throughout the turnaround.
- Manage seats, upgrades, standby travelers, carry-on restrictions, and passenger accommodations.
- Operate the jetbridge in accordance with airline procedures and confirm that it is positioned safely for boarding and departure.
- During disruptions or oversales, communicate updates, seek volunteers when applicable, rebook passengers, and complete required denied-boarding documentation.
- Complete or provide the information needed for the flight load closeout, including final passenger and cargo counts. The flight crew uses this information for weight-and-balance and performance calculations; the exact workflow and ownership vary by airline and ground handler.

```mermaid
flowchart TD
    A[Arrive at gate] --> B[Review flight details and operational updates]
    B --> C[Check in crew and coordinate with operations]
    C --> D[Open gate and prepare boarding equipment and jetbridge]
    D --> E[Handle passenger questions, accommodations, seats, upgrades, and standby]
    E --> F{Flight on schedule?}

    F -->|Yes| G[Announce boarding groups]
    G --> H[Verify ID and boarding pass]
    H --> I[Scan passengers and manage carry-on bags]
    I --> J[Reconcile final passenger and cargo counts]
    J --> K[Complete or provide load-closeout information]
    K --> L[Coordinate with crew, ramp, and operations]
    L --> M[Close boarding, secure jetbridge, and confirm departure]
    M --> N[Finalize departure records]

    F -->|No: delay, cancellation, or oversell| O[Announce disruption and explain options]
    O --> P[Coordinate with operations and flight crew]
    P --> Q[Rebook passengers or request volunteers]
    Q --> R[Process compensation or denied-boarding documents]
    R --> E
```
