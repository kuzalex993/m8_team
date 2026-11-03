# reward-order-resolution Specification

## Purpose

Обеспечить принятие администратором окончательного решения по заказу награды с сохранением согласованности заявки, баланса пользователя и истории операций.

## Requirements

### Requirement: Cancellation is restricted to pending orders
The system SHALL allow an administrator to cancel an individual reward order only while its status is `new`, identifying the order by its unique request ID.

#### Scenario: Cancel a pending order
- **WHEN** an administrator cancels an order with status `new`
- **THEN** the order becomes `cancelled` with a decision date

#### Scenario: Cancel a resolved order
- **WHEN** cancellation is attempted for a `completed` or `cancelled` order
- **THEN** no balance, ledger or order changes occur

#### Scenario: User cannot cancel
- **WHEN** a regular user views their reward orders
- **THEN** no administrator cancellation action is available

### Requirement: Cancellation refunds atomically
The system SHALL commit the order cancellation, decrease of reserved bonuses, increase of free bonuses and one `refund bonus` entry in `user_bonus` as one atomic operation. The ledger entry SHALL contain the owner user ID, positive refunded amount, `event_type = user_reward`, `event_id` equal to the request ID and a timestamp.

#### Scenario: Successful refund
- **WHEN** a pending order with a verified reservation of 100 bonuses is cancelled
- **THEN** its owner's free balance increases by 100, reserved balance decreases by 100, one linked refund entry is created and the order is cancelled

#### Scenario: Write failure
- **WHEN** cancellation cannot commit
- **THEN** no partial changes to balances, ledger or order persist and the administrator sees an error

### Requirement: Refund uses the original reservation
The system SHALL return exactly the amount reserved for that order, independently of catalogue price changes or deletion. All orders SHALL use the amount from exactly one `reserve bonus` entry in `user_bonus` whose `event_id` equals the request ID and whose owner matches the order owner. Missing, ambiguous, invalid or inconsistent reservation evidence SHALL prevent cancellation without any writes.

#### Scenario: Catalogue changes
- **WHEN** a 100-bonus order is cancelled after its catalogue price changes or the catalogue item is deleted
- **THEN** exactly 100 bonuses are returned

#### Scenario: Reservation identifies the order
- **WHEN** an order has one valid matching reservation ledger entry with `event_id` equal to the request ID
- **THEN** cancellation uses that entry's amount regardless of the reservation document's own ID

#### Scenario: Invalid reservation
- **WHEN** reservation evidence is missing, ambiguous, has a mismatched owner, or exceeds the user's reserved balance
- **THEN** cancellation makes no changes and reports an error

### Requirement: Resolution is safe under concurrent operations
The system SHALL allow at most one terminal decision per order. Retries and concurrent cancellation or confirmation SHALL NOT duplicate refunds, debits or state transitions.

#### Scenario: Repeated cancellation
- **WHEN** cancellation is submitted twice for one order
- **THEN** at most one refund is recorded and balances change once

#### Scenario: Confirmation races cancellation
- **WHEN** administrators confirm and cancel the same pending order concurrently
- **THEN** only one decision succeeds and balances and ledger agree with that decision

#### Scenario: Two orders of one user
- **WHEN** two distinct pending orders of one user are cancelled concurrently
- **THEN** each order is refunded once and the final balances include both refunds

### Requirement: Admin UI reflects committed cancellation
The system SHALL show «Отменить» on pending reward cards, remove a card from active requests only after successful cancellation, and preserve the cancelled order in history. Cancellation failure SHALL leave the pending card available and show a Russian error message.

#### Scenario: Card disappears after success
- **WHEN** cancellation succeeds from the pending card
- **THEN** the active list refreshes, the card disappears and history shows the cancelled order

#### Scenario: Card remains after failure
- **WHEN** cancellation fails before committing
- **THEN** the pending card remains and the administrator sees a Russian error message
