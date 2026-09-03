# Gate Agent Routine at the Ticket Counter

## Key Responsibilities

- Welcome passengers, retrieve reservations, and apply the airline's ticketing and baggage rules.
- Verify identification, required travel documents, and destination-specific entry requirements before check-in.
- Issue or amend tickets, assign seats, check flight loads, identify codeshare itineraries, and rebook passengers when needed.
- Accept, tag, and receipt checked baggage; collect applicable fees; and provide boarding, gate, and connection information.
- Use the airline's departure-control and reservation systems accurately, including the command sequences needed for check-in, ticketing, flight loads, and rebooking.
- At smaller or outstation airports, cross-trained agents may alternate between the ticket counter and gate duties during the same shift.

```mermaid
flowchart TD
    A[Open ticket counter] --> B[Review flight schedules, alerts, and travel requirements]
    B --> C[Prepare check-in systems, printers, and baggage tags]
    C --> D[Welcome passenger and retrieve reservation]
    D --> E[Verify ID, documents, and destination requirements]
    E --> F{Reservation and documents valid?}

    F -->|Yes| G[Confirm itinerary, seat, baggage, and special-service requests]
    G --> H[Issue or amend ticket and process any rebooking]
    H --> I[Accept and tag checked baggage]
    I --> J[Collect applicable fees]
    J --> K[Issue boarding pass and baggage receipt]
    K --> L[Give gate, boarding, and connection information]
    L --> M[Complete check-in and assist next passenger]

    F -->|No| N[Explain issue and review available options]
    N --> O[Correct reservation, rebook, or request supervisor support]
    O --> P{Issue resolved?}
    P -->|Yes| G
    P -->|No| Q[Provide next steps and document the interaction]
    Q --> M
```